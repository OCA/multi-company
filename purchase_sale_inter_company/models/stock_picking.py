# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking", copy=False)

    def action_done(self):
        # Only DropShip pickings
        po_picks = self.browse()
        for pick in self.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        ).sudo():
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue
            purchase.picking_ids.write({"intercompany_picking_id": pick.id})
            for move_line in pick.move_line_ids:
                qty_done = move_line.qty_done
                sale_line_id = move_line.move_id.sale_line_id
                po_move_lines = sale_line_id.auto_purchase_line_id.move_ids.mapped(
                    "move_line_ids"
                )
                for po_move_line in po_move_lines:
                    if po_move_line.product_qty >= qty_done:
                        po_move_line.qty_done = qty_done
                        qty_done = 0.0
                    else:
                        po_move_line.qty_done = po_move_line.product_qty
                        qty_done -= po_move_line.product_qty
                    po_picks |= po_move_line.picking_id
                if qty_done and po_move_lines:
                    po_move_lines[-1:].qty_done += qty_done
                elif not po_move_lines:
                    raise UserError(
                        _(
                            "There's no corresponding line in PO %s for assigning "
                            "qty from %s for product %s"
                        )
                        % (purchase.name, pick.name, move_line.product_id.name)
                    )
        # Transfer dropship pickings
        for po_pick in po_picks.sudo():
            po_pick.with_company(po_pick.company_id.id).action_done()
        return super(StockPicking, self).action_done()

    def button_validate(self):
        is_intercompany = self.env["res.company"].search(
            [("partner_id", "=", self.partner_id.id)]
        ) or self.env["res.company"].search(
            [("partner_id", "=", self.partner_id.parent_id.id)]
        )
        if (
            is_intercompany
            and self.company_id.sync_picking
            and self.picking_type_code == "outgoing"
        ):
            sale_order = self.sale_id
            src_pickings = sale_order.picking_ids.filtered(
                lambda l: l.state in ["draft", "waiting", "confirmed", "assigned"]
            )
            dest_company = sale_order.partner_id.ref_company_ids
            for src_picking in src_pickings:
                src_picking._sync_receipt_with_delivery(
                    dest_company,
                    sale_order,
                    src_pickings,
                )
        return super().button_validate()

    @api.model
    def _prepare_picking_line_data(self, src_picking, dest_picking):
        self.ensure_one()
        if self.check_all_done(src_picking):
            for line in src_picking.sudo().move_ids_without_package:
                line.write({"quantity_done": line.reserved_availability})
        for src_line in src_picking.sudo().move_ids_without_package:
            if (
                src_line.product_id
                in dest_picking.sudo().move_ids_without_package.mapped("product_id")
                and src_line.quantity_done > 0
            ):
                dest_move = dest_picking.sudo().move_ids_without_package.filtered(
                    lambda m: m.product_id == src_line.product_id
                )
                dest_move.write(
                    {"quantity_done": dest_move.quantity_done + src_line.quantity_done}
                )

    @api.multi
    def _sync_receipt_with_delivery(self, dest_company, sale_order, src_pickings):
        self.ensure_one()
        intercompany_user = dest_company.intercompany_user_id
        purchase_order = (
            self.sudo(intercompany_user.id)
            .env["purchase.order"]
            .search(
                [
                    ("partner_ref", "=", sale_order.name),
                    ("company_id", "=", dest_company.id),
                ]
            )
        )
        if (
            not purchase_order
            or not purchase_order.sudo(intercompany_user.id).picking_ids
        ):
            raise UserError(_("PO does not exist or has no receipts"))
        receipts = purchase_order.sudo(intercompany_user.id).picking_ids
        for src_picking in src_pickings.sudo().filtered(lambda l: l.state != "done"):
            dest_picking = receipts.sudo().filtered(
                lambda r: not r.intercompany_picking_id
                or r.intercompany_picking_id.id == src_picking.id
            )
            if not dest_picking:
                dest_picking = receipts.sudo().filtered(
                    lambda r: r.state not in ["done", "draft", "cancel"]
                )
            if (
                dest_picking
                and src_picking.state not in ["done", "cancel"]
                and sum(src_picking.mapped("move_ids_without_package.quantity_done"))
                > 0
                or self.check_all_done(src_picking)
            ):
                dest_picking._prepare_picking_line_data(
                    src_picking,
                    dest_picking,
                )
                dest_picking.write(
                    {
                        "intercompany_picking_id": src_picking.id,
                    }
                )
                src_picking.sudo().write(
                    {
                        "intercompany_picking_id": dest_picking.id,
                    }
                )
                dest_picking.action_confirm()

    def check_all_done(self, picking):
        picking_lines = picking.move_ids_without_package.filtered(
            lambda l: l.state != "cancel"
        )
        qty_done = sum(picking_lines.mapped("quantity_done"))
        reserved = sum(picking_lines.mapped("reserved_availability"))
        available = sum(picking_lines.mapped("product_uom_qty"))
        if qty_done == 0.0 and reserved == available:
            return True
        return False

    def action_generate_backorder_wizard(self):
        view = self.env.ref("stock.view_backorder_confirmation")
        wiz = (
            self.env["stock.backorder.confirmation"]
            .with_context(picking_id=self.id)
            .create({"pick_ids": [(4, p.id) for p in self]})
        )
        return {
            "name": _("Create Backorder?"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.backorder.confirmation",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": wiz.id,
            "context": self.env.context,
        }
