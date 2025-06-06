# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking", copy=False)

    def _set_intercompany_picking_qty_and_lot(self, purchase):
        self.ensure_one()
        po_picking_pending = purchase.picking_ids.filtered(
            lambda x: x.state not in ["done", "cancel"]
        )
        po_picking_pending.intercompany_picking_id = self.id
        if not self.intercompany_picking_id and po_picking_pending[0]:
            self.intercompany_picking_id = po_picking_pending[0]
        for move in self.move_ids:
            move_lines = move.move_line_ids.filtered(lambda x: x.quantity > 0)
            po_move_pending = move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                lambda x, ic_pick=self.intercompany_picking_id: x.picking_id == ic_pick
                and x.state not in ["done", "cancel"]
            )
            po_move_lines = po_move_pending.mapped("move_line_ids")
            move_line_diff = len(move_lines) - len(po_move_lines)
            # generate new move lines or remove if needed
            # example: In purchase order of C1, we have 2 move lines
            # and in reception of C2, we have 3 move lines(with lot or serial number)
            # then we need to create 1 more move line in purchase order of C1
            if move_line_diff > 0:
                new_move_line_vals = []
                for _index in range(move_line_diff):
                    vals = po_move_pending._prepare_move_line_vals()
                    new_move_line_vals.append(vals)
                po_move_lines |= po_move_lines.create(new_move_line_vals)
            elif move_line_diff < 0:
                # remove the extra move lines in the receipt of lot tracking product
                # example: In the receipt, we have 3 move lines for 3 different serials,
                # in the delivery we specify 2 serials. When validating the delivery and
                # creating back order, Odoo generates 3 move lines in the receipt, so
                # we need to remove 1 different move line in the receipt, otherwise it
                # will cause an error saying that we need to assign a lot or serial
                # for the remaining move line
                po_move_lines[len(move_lines) :].unlink()
                po_move_lines = po_move_lines[: len(move_lines)]
            # check and assign lots and quantity here
            for ml, po_ml in zip(move_lines, po_move_lines, strict=True):
                po_ml.quantity = ml.quantity
                if not ml.lot_id:
                    continue
                # search if the same lot exists in destination company
                dest_lot = ml._get_or_create_lot_intercompany(po_ml.company_id)
                po_ml.lot_id = dest_lot
        return po_picking_pending

    def _action_done(self):
        # Only DropShip pickings
        po_picks = self.browse()
        for pick in self.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        ).sudo():
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue

            po_picks |= pick._set_intercompany_picking_qty_and_lot(purchase)

            # Call pre-action hook to update 'picked' cause only picked lines
            # are processed
            # Transfer dropship pickings
            for po_pick in po_picks.sudo():
                po_pick.with_company(po_pick.company_id.id)._pre_action_done_hook()
                po_pick.with_company(po_pick.company_id.id)._action_done()
        return super()._action_done()
