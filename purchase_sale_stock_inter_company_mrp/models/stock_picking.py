# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_product_intercompany_qty_done_dict(self, sale_move_lines, po_move_lines):
        sale_move = sale_move_lines.move_id[:1]
        po_move = po_move_lines.move_id[:1]
        sale_bom = sale_move.bom_line_id.bom_id
        purchase_bom = po_move.bom_line_id.bom_id
        if not sale_bom and not purchase_bom:
            return super()._get_product_intercompany_qty_done_dict(
                sale_move_lines, po_move_lines
            )
        sale_line = sale_move.sale_line_id
        # The sync loop passes one sale move line at a time: use every done
        # move of the sale line in this picking to get the whole quantity
        sale_moves = self.move_ids.filtered(
            lambda m: m.sale_line_id == sale_line and m.state == "done"
        )
        product = po_move.product_id
        # Sale Kit: kits delivered based on the components delivered
        if sale_bom:
            order_qty = sale_line.product_uom_id._compute_quantity(
                sale_line.product_uom_qty, sale_bom.uom_id
            )
            filters = {
                "incoming_moves": lambda m: True,
                "outgoing_moves": lambda m: False,
            }
            kit_qty = sale_moves.filtered(
                lambda m: m.bom_line_id.bom_id == sale_bom
            )._compute_kit_quantities(
                sale_line.product_id, order_qty, sale_bom, filters
            )
            qty_done, qty_uom = kit_qty, sale_bom.uom_id
        else:
            qty_done = sum(sale_moves.mapped("quantity_product_uom"))
            qty_uom = sale_line.product_id.uom_id
        if not purchase_bom:
            return {product: qty_uom._compute_quantity(qty_done, po_move_lines.uom_id)}
        # Purchase Kit: components received based on the kits delivered
        factor = (
            qty_uom._compute_quantity(qty_done, purchase_bom.uom_id)
            / purchase_bom.product_qty
        )
        _boms, bom_sub_lines = purchase_bom.explode(
            product, factor, picking_type=purchase_bom.picking_type_id
        )
        qty_by_bom_line = {
            bom_line: bom_line_data["qty"] for bom_line, bom_line_data in bom_sub_lines
        }
        # The sync loop only writes the purchase move line zipped with the
        # sale move line: set the quantity of the other component moves
        po_moves = po_move.purchase_line_id.move_ids.filtered(
            lambda m: (
                m.picking_id == po_move.picking_id and m.state not in ["done", "cancel"]
            )
        )
        res = {}
        for move in po_moves:
            qty = move.bom_line_id.uom_id._compute_quantity(
                qty_by_bom_line.get(move.bom_line_id, 0.0), move.uom_id
            )
            if move == po_move:
                res[move.product_id] = move.uom_id._compute_quantity(
                    qty, po_move_lines.uom_id
                )
                continue
            move._set_quantity_done(qty)
            move.picked = not move.uom_id.is_zero(qty)
        return res
