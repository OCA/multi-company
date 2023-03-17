# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking")

    def _action_done(self):
        # Only DropShip pickings
        so_picks = self.browse()
        for pick in self.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        ).sudo():
            sale = pick.purchase_id.auto_sale_order_id
            if not sale:
                continue
            sale.picking_ids.write({"intercompany_picking_id": pick.id})
            for move_line in pick.move_line_ids:
                qty_done = move_line.qty_done
                purchase_line_id = move_line.move_id.purchase_line_id
                so_move_lines = purchase_line_id.auto_sale_line_id.move_ids.mapped(
                    "move_line_ids"
                )
                for so_move_line in so_move_lines:
                    if so_move_line.product_qty >= qty_done:
                        so_move_line.qty_done = qty_done
                        qty_done = 0.0
                    else:
                        so_move_line.qty_done = so_move_line.product_qty
                        qty_done -= so_move_line.product_qty
                    so_picks |= so_move_line.picking_id
                if qty_done and so_move_lines:
                    so_move_lines[-1:].qty_done += qty_done
                elif not so_move_lines:
                    raise UserError(
                        _(
                            "There's no corresponding line in SO %(so)s for assigning "
                            "qty from %(pick_name)s for product %(product)s"
                        )
                        % (
                            {
                                "so": sale.name,
                                "pick_name": pick.name,
                                "product": move_line.product_id.name,
                            }
                        )
                    )
        # Transfer dropship pickings
        for so_pick in so_picks.sudo():
            so_pick.with_company(so_pick.company_id.id)._action_done()
        return super()._action_done()
