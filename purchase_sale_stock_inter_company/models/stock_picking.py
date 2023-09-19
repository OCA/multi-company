# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking", copy=False)

    def _get_product_intercompany_qty_done_dict(self, sale_move_lines, po_move_lines):
        product = po_move_lines[0].product_id
        qty_done = sum(sale_move_lines.mapped("qty_done"))
        res = {product: qty_done}
        return res

    def _set_intercompany_picking_qty(self, purchase):
        po_picks = self.browse()
        sale_line_ids = self.move_line_ids.mapped("move_id.sale_line_id")
        for sale_line in sale_line_ids:
            sale_move_lines = self.move_line_ids.filtered(
                lambda ml: ml.move_id.sale_line_id == sale_line
            )
            po_move_lines = sale_line.auto_purchase_line_id.move_ids.mapped(
                "move_line_ids"
            )
            if not po_move_lines:
                raise UserError(
                    _(
                        "There's no corresponding line in PO %(po)s for assigning "
                        "qty from %(pick_name)s for product %(product)s"
                    )
                    % (
                        {
                            "po": purchase.name,
                            "pick_name": self.name,
                            "product": sale_line.product_id.name,
                        }
                    )
                )
            product_qty_done = self._get_product_intercompany_qty_done_dict(
                sale_move_lines, po_move_lines
            )
            for product, qty_done in product_qty_done.items():
                product_po_mls = po_move_lines.filtered(
                    lambda x: x.product_id == product
                )
                for po_move_line in product_po_mls:
                    if po_move_line.reserved_qty >= qty_done:
                        po_move_line.qty_done = qty_done
                        qty_done = 0.0
                    elif po_move_line.reserved_qty:
                        po_move_line.qty_done = po_move_line.reserved_qty
                        qty_done -= po_move_line.reserved_qty
                    po_picks |= po_move_line.picking_id
                if qty_done and product_po_mls:
                    product_po_mls[-1:].qty_done += qty_done
        return po_picks

    def _action_done(self):
        # Only DropShip pickings
        po_picks = self.browse()
        for pick in self.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        ).sudo():
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue
            purchase.picking_ids.write({"intercompany_picking_id": pick.id})
            if not pick.intercompany_picking_id and purchase.picking_ids[0]:
                pick.write({"intercompany_picking_id": purchase.picking_ids[0]})
            po_picks |= pick._set_intercompany_picking_qty(purchase)
            for move_line in pick.move_line_ids:
                sale_line_id = move_line.move_id.sale_line_id
                po_move_lines = sale_line_id.auto_purchase_line_id.move_ids.mapped(
                    "move_line_ids"
                )
                if not po_move_lines:
                    raise UserError(
                        _(
                            "There's no corresponding line in PO %s for assigning "
                            "qty from %s for product %s"
                        )
                        % (purchase.name, pick.name, move_line.product_id.name)
                    )
        return super()._action_done()

    def button_validate(self):
        res = super().button_validate()
        is_intercompany = self.env["res.company"].search(
            [("partner_id", "=", self.partner_id.id)]
        ) or self.env["res.company"].search(
            [("partner_id", "=", self.partner_id.parent_id.id)]
        )
        if (
            is_intercompany
            and self.company_id.sync_picking
            and self.state == "done"
            and self.picking_type_code == "outgoing"
        ):
            sale_order = self.sale_id
            dest_company = sale_order.partner_id.ref_company_ids
            for rec in self:
                if rec.intercompany_picking_id:
                    rec._sync_receipt_with_delivery(
                        dest_company,
                        sale_order,
                    )
        return res

    def _sync_receipt_with_delivery(self, dest_company, sale_order):
        self.ensure_one()
        intercompany_user = dest_company.intercompany_sale_user_id
        purchase_order = sale_order.auto_purchase_order_id.sudo()
        if not (purchase_order and purchase_order.picking_ids):
            raise UserError(_("PO does not exist or has no receipts"))
        if self.intercompany_picking_id:
            dest_picking = self.intercompany_picking_id.with_user(intercompany_user.id)
            for picking_line in self.move_line_ids_without_package.sorted("qty_done"):
                dest_picking_line = (
                    dest_picking.sudo().move_line_ids_without_package.filtered(
                        lambda l: l.product_id.id == picking_line.product_id.id
                    )
                )
                dest_picking_line.sudo().write(
                    {
                        "qty_done": picking_line.qty_done,
                    }
                )
            for picking_move in self.move_ids_without_package.sorted("quantity_done"):
                dest_picking_move = (
                    dest_picking.sudo().move_ids_without_package.filtered(
                        lambda l: l.product_id.id == picking_move.product_id.id
                    )
                )
                dest_picking_move.sudo().write(
                    {
                        "quantity_done": picking_move.quantity_done,
                    }
                )
            dest_picking.sudo().with_context(
                cancel_backorder=bool(
                    self.env.context.get("picking_ids_not_to_backorder")
                )
            )._action_done()

    def _update_extra_data_in_picking(self, picking):
        if hasattr(self, "_cal_weight"):  # from delivery module
            self._cal_weight()