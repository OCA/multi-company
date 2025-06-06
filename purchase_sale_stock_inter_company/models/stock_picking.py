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

            # START CHANGES FROM V13
            po_picking_pending = purchase.picking_ids.filtered(
                lambda x: x.state not in ["done", "cancel"]
            )
            po_picking_pending.intercompany_picking_id = pick.id
            if not pick.intercompany_picking_id and po_picking_pending[0]:
                pick.intercompany_picking_id = po_picking_pending[0]
            for move in pick.move_lines:
                move_lines = move.move_line_ids.filtered(lambda x: x.qty_done > 0)
                po_move_pending = (
                    move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                        lambda x, ic_pick=pick.intercompany_picking_id: x.picking_id
                        == ic_pick
                        and x.state not in ["done", "cancel"]
                    )
                )
                po_move_lines = po_move_pending.mapped("move_line_ids")
                move_line_diff = len(move_lines) - len(po_move_lines)
                # generate new move lines if needed
                # example: In purchase order of C1, we have 2 move lines
                # and in reception of C2, we have 3 move lines(with lot or serial number)
                # then we need to create 1 more move line in purchase order of C1
                if move_line_diff > 0:
                    new_move_line_vals = []
                    for _index in range(move_line_diff):
                        vals = po_move_pending._prepare_move_line_vals()
                        new_move_line_vals.append(vals)
                    po_move_lines |= po_move_lines.create(new_move_line_vals)
                # check and assign lots here
                # if len(move_lines) != (po_move_lines)
                # the zip will stop at the shortest list(only with qty_done > 0)
                # list(zip([1, 2], [1, 2, 3, 4])) = [(1, 1), (2, 2)]
                # list(zip([1, 2, 3, 4], [1, 2])) = [(1, 1), (2, 2)]
                for ml, po_ml in zip(move_lines, po_move_lines):
                    lot_id = ml.lot_id
                    if not lot_id:
                        continue
                    # search if the same lot exists in destination company
                    dest_lot = ml._get_or_create_lot_intercompany(po_ml.company_id)
                    po_ml.lot_id = dest_lot
        return super()._action_done()
