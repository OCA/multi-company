# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking")

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
            po_picks |= pick._set_intercompany_picking_qty(purchase)
        # Transfer dropship pickings
        for po_pick in po_picks.sudo():
            po_pick.with_company(po_pick.company_id.id)._action_done()
        return super()._action_done()
