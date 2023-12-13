# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking")

    def action_done(self):
        for pick in self.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        ).sudo():
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue
            purchase.picking_ids.write({"intercompany_picking_id": pick.id})
            if not pick.intercompany_picking_id and purchase.picking_ids[0]:
                pick.write({"intercompany_picking_id": purchase.picking_ids[0]})
            for move in pick.move_lines:
                move_lines = move.move_line_ids
                po_move_lines = move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                    lambda x, ic_pick=pick.intercompany_picking_id: x.picking_id
                    == ic_pick
                ).mapped(
                    "move_line_ids"
                )
                if not len(move_lines) == len(po_move_lines):
                    raise UserError(
                        _(
                            "Mismatch between move lines with the "
                            "corresponding  PO %s for assigning "
                            "quantities and lots from %s for product %s"
                        )
                        % (purchase.name, pick.name, move.product_id.name)
                    )
                # check and assign lots here
                for ml, po_ml in zip(move_lines, po_move_lines):
                    lot_id = ml.lot_id
                    if not lot_id:
                        continue
                    # search if the same lot exists in destination company
                    dest_lot_id = (
                        self.env["stock.production.lot"]
                        .sudo()
                        .search(
                            [
                                ("product_id", "=", lot_id.product_id.id),
                                ("name", "=", lot_id.name),
                                ("company_id", "=", po_ml.company_id.id),
                            ],
                            limit=1,
                        )
                    )
                    if not dest_lot_id:
                        # if it doesn't exist, create it by copying from original company
                        dest_lot_id = lot_id.copy({"company_id": po_ml.company_id.id})
                    po_ml.lot_id = dest_lot_id
        return super().action_done()
