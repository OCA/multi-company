# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import float_is_zero, float_round


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_product_intercompany_qty_done_dict(self, sale_move_lines, po_move_lines):
        sale_bom = sale_move_lines[0].move_id.bom_line_id.bom_id
        purchase_bom = po_move_lines[0].move_id.bom_line_id.bom_id
        if not sale_bom and not purchase_bom:
            return super()._get_product_intercompany_qty_done_dict(
                sale_move_lines, po_move_lines
            )
        res = {}
        product = po_move_lines[0].product_id
        sale_qty_done = sum(sale_move_lines.mapped("qty_done"))
        # Sale Kit: get kit product qty done based on the move lines qty done
        if sale_bom:
            sale_line = sale_move_lines[0].move_id.sale_line_id
            order_qty = sale_line.product_uom._compute_quantity(
                sale_line.product_uom_qty, sale_bom.product_uom_id
            )
            kit_qty = self._compute_kit_quantities_done(
                sale_move_lines.mapped("move_id"),
                sale_line.product_id,
                order_qty,
                sale_bom,
            )
            sale_qty_done = sale_bom.product_uom_id._compute_quantity(
                kit_qty, sale_line.product_id.uom_id
            )
        # Purchase Kit: get components qty done based on the sale qty done
        if purchase_bom:
            _, bom_sub_lines = purchase_bom.explode(product, sale_qty_done)
            for bom_line, bom_line_data in bom_sub_lines:
                res[bom_line.product_id] = bom_line_data["qty"]
            return res
        res[product] = sale_qty_done
        return res

    def _compute_kit_quantities_done(self, move_ids, product_id, kit_qty, kit_bom):
        """Based on Odoo standard _compute_kit_quantities method.
        We use the quantity_done of the moves instead of the product_qty.
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
            bom_line_moves = move_ids.filtered(lambda m: m.bom_line_id == bom_line)
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
                # Use quantity_done to get the qty_processed of each component
                qty_processed = sum(bom_line_moves.mapped("quantity_done"))
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
