# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import float_is_zero, float_round


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done_intercompany_actions(self, purchase):
        self.ensure_one()
        po_picking_pending = purchase.picking_ids.filtered(
            lambda x: x.state not in ["done", "cancel"]
        )
        if not self.intercompany_picking_id and po_picking_pending:
            dest_picking = po_picking_pending[0]
        else:
            dest_picking = self.intercompany_picking_id
        if dest_picking:
            processed_sale_lines = set()
            for move in self.move_ids:
                if not self._is_intercompany_purchase_kit_move(move, dest_picking):
                    continue
                sale_line = move.sale_line_id
                if sale_line.id in processed_sale_lines:
                    continue
                processed_sale_lines.add(sale_line.id)
                po_move_pending = sale_line.auto_purchase_line_id.move_ids.filtered(
                    lambda x, dp=dest_picking: x.picking_id == dp
                    and x.state not in ["done", "cancel"]
                )
                purchase_bom = po_move_pending[0].bom_line_id.bom_id
                all_sale_moves = self.move_ids.filtered(
                    lambda m, sl=sale_line: m.sale_line_id == sl
                )
                sale_bom = all_sale_moves[0].bom_line_id.bom_id
                if sale_bom:
                    order_qty = sale_line.product_uom._compute_quantity(
                        sale_line.product_uom_qty, sale_bom.product_uom_id
                    )
                    kit_qty = self._compute_kit_quantities_done(
                        all_sale_moves,
                        sale_line.product_id,
                        order_qty,
                        sale_bom,
                    )
                    sale_qty_done = sale_bom.product_uom_id._compute_quantity(
                        kit_qty, sale_line.product_id.uom_id
                    )
                else:
                    sale_qty_done = sum(
                        all_sale_moves.mapped("move_line_ids")
                        .filtered(lambda ml: ml.quantity > 0)
                        .mapped("quantity")
                    )
                _, bom_sub_lines = purchase_bom.explode(
                    sale_line.product_id, sale_qty_done
                )
                qty_by_product = {
                    bom_line.product_id: bom_line_data["qty"]
                    for bom_line, bom_line_data in bom_sub_lines
                }
                for po_move in po_move_pending:
                    qty = qty_by_product.get(po_move.product_id, 0.0)
                    po_move.move_line_ids.write({"quantity": qty, "picked": True})
        return super()._action_done_intercompany_actions(purchase)

    def _get_product_intercompany_qty_done_dict(self, sale_move_lines, po_move_lines):
        sale_bom = sale_move_lines.move_id.bom_line_id.bom_id
        if not sale_bom:
            return super()._get_product_intercompany_qty_done_dict(
                sale_move_lines, po_move_lines
            )
        # sale_kit : N sale moves (components) → 1 po move (final kit product)
        sale_line = sale_move_lines.move_id.sale_line_id
        order_qty = sale_line.product_uom._compute_quantity(
            sale_line.product_uom_qty, sale_bom.product_uom_id
        )
        # All moves for kit, not only current pair
        all_sale_moves = self.move_ids.filtered(
            lambda m, sl=sale_line: m.sale_line_id == sl and m.bom_line_id
        )
        kit_qty = self._compute_kit_quantities_done(
            all_sale_moves,
            sale_line.product_id,
            order_qty,
            sale_bom,
        )
        sale_qty_done = sale_bom.product_uom_id._compute_quantity(
            kit_qty, sale_line.product_id.uom_id
        )
        return {po_move_lines.product_id: sale_qty_done}

    def _compute_kit_quantities_done(self, move_ids, product_id, kit_qty, kit_bom):
        """Based on Odoo standard _compute_kit_quantities method.
        We use the quantity of the moves instead of the product_qty.
        """
        qty_ratios = []
        boms, bom_sub_lines = kit_bom.explode(product_id, kit_qty)
        for bom_line, bom_line_data in bom_sub_lines:
            # skip service since we never deliver them
            if bom_line.product_id.type == "service":
                continue
            if float_is_zero(
                bom_line_data["qty"],
                precision_rounding=bom_line.product_uom_id.rounding,
            ):
                # As BoMs allow components with 0 qty, a.k.a. optionnal components,
                # we simply skip those to avoid a division by zero.
                continue
            bom_line_moves = move_ids.filtered(lambda m, b=bom_line: m.bom_line_id == b)
            if bom_line_moves:
                # We compute the quantities needed of each components to make one kit.
                # Then, we collect every relevant moves related to a specific component
                # to know how many are considered delivered.
                uom_qty_per_kit = bom_line_data["qty"] / bom_line_data["original_qty"]
                qty_per_kit = bom_line.product_uom_id._compute_quantity(
                    uom_qty_per_kit, bom_line.product_id.uom_id, round=False
                )
                if not qty_per_kit:
                    continue
                # Use quantity to get the qty_processed of each component
                qty_processed = sum(bom_line_moves.mapped("quantity"))
                # We compute a ratio to know how many kits we can produce with this
                # quantity of that specific component
                qty_ratios.append(
                    float_round(
                        qty_processed / qty_per_kit,
                        precision_rounding=bom_line.product_id.uom_id.rounding,
                    )
                )
            else:
                return 0.0
        if qty_ratios:
            # Now that we have every ratio by components, we keep the lowest one to
            # know how many kits we can produce with the quantities delivered of each
            # component. We use the floor division here because a 'partial kit'
            # doesn't make sense.
            return min(qty_ratios) // 1
        else:
            return 0.0

    def _is_intercompany_purchase_kit_move(self, move, dest_picking):
        po_move_pending = move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
            lambda x, dp=dest_picking: x.picking_id == dp
            and x.state not in ["done", "cancel"]
        )
        return bool(po_move_pending and po_move_pending[0].bom_line_id.bom_id)
