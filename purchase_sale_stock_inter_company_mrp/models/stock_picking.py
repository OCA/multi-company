# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

# The moves passed to _compute_kit_quantities are all done incoming moves of
# the sale picking, so there is nothing to exclude nor to subtract.
KIT_QUANTITIES_FILTERS = {
    "incoming_moves": lambda m: True,
    "outgoing_moves": lambda m: False,
}


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_intercompany_kit_bom(self, product, company):
        """Return the phantom BOM of the kit in the given company.

        The BOM is resolved from the product because with nested phantom
        BOMs the component moves point to a sub-BOM through their
        ``bom_line_id``, while the sync needs the top-level kit BOM.
        """
        return self.env["mrp.bom"]._bom_find(
            product, company_id=company.id, bom_type="phantom"
        )[product]

    def _set_intercompany_kit_quantities_done(self, purchase, dest_picking):
        """Define the kit quantities received on the reception picking.

        Kits are handled here because the sale and purchase sides may have
        different move structures, depending on where the phantom BOM is
        defined:

        * 'purchase-kit':
            - BOM on the PO side, the purchase picking receives components
              (N moves);
            - no BOM on the SO side, the sale picking delivers the kit
              product (1 move);
        * 'sale-kit':
            - no BOM on the PO side, the purchase side receives the kit
              product (1 move);
            - BOM on the SO side, the sale side delivers components
              (N moves);
        * 'sale-purchase-kit':
            - BOM on both sides (possibly different);
            - both pickings hold component moves.

        In every case the number of kits received equals the number of kits
        delivered (the same goods are sold and purchased); only the BOM and
        UoM used to decompose them may differ.
        """
        processed_sale_lines = set()
        for sale_move in self.move_ids:
            sale_line = sale_move.sale_line_id
            purchase_pending_moves = self._get_intercompany_purchase_pending_moves(
                sale_line, dest_picking
            )
            if not purchase_pending_moves.bom_line_id:
                # The 'sale-kit' situation is not handled here, but in the
                # `_get_product_intercompany_qty_done_dict()` override.
                continue
            # In a 'sale-purchase-kit' situation, process all the component
            # moves of a sale line at once when going through the first
            # component move (skip the other ones related to the same line).
            if sale_line.id in processed_sale_lines:
                continue
            processed_sale_lines.add(sale_line.id)
            purchase_bom = self._get_intercompany_kit_bom(
                sale_line.product_id, purchase.company_id
            )
            all_sale_moves = self.move_ids.filtered(
                lambda m, sl=sale_line: m.sale_line_id == sl
            )
            sale_bom = self._get_intercompany_kit_bom(
                sale_line.product_id, sale_line.company_id
            )
            if sale_bom:
                # 'sale-purchase-kit' situation: recompute how many kits were
                # delivered from the components actually shipped.
                kit_qty_sold = sale_line.product_uom._compute_quantity(
                    sale_line.product_uom_qty, sale_bom.product_uom_id
                )
                kit_qty_done = all_sale_moves._compute_kit_quantities(
                    sale_line.product_id, kit_qty_sold, sale_bom, KIT_QUANTITIES_FILTERS
                )
                sale_qty_done = sale_bom.product_uom_id._compute_quantity(
                    kit_qty_done, sale_line.product_id.uom_id
                )
            else:
                # 'purchase-kit' situation: the delivered quantity is the kit
                # move quantity (len(all_sale_moves) == 1).
                sale_qty_done = sum(
                    all_sale_moves.mapped("move_line_ids")
                    .filtered(lambda ml: ml.quantity > 0)
                    .mapped("quantity")
                )
            # The kits received equal the kits delivered: express
            # sale_qty_done in the purchase BOM UoM before exploding it.
            purchase_qty_done = sale_line.product_id.uom_id._compute_quantity(
                sale_qty_done, purchase_bom.product_uom_id
            )
            _, purchase_bom_lines = purchase_bom.explode(
                sale_line.product_id, purchase_qty_done / purchase_bom.product_qty
            )
            # Map each purchase BOM line to its quantity, kept in the line UoM.
            qty_done_by_bom_line = {
                bom_line: bom_line_data["qty"]
                for bom_line, bom_line_data in purchase_bom_lines
            }
            for purchase_move in purchase_pending_moves:
                # each purchase move's qty done comes from its BOM line's qty.
                qty_done = qty_done_by_bom_line.get(purchase_move.bom_line_id, 0.0)
                purchase_move._set_quantity_done(
                    purchase_move.bom_line_id.product_uom_id._compute_quantity(
                        qty_done, purchase_move.product_uom
                    )
                )
                purchase_move.picked = True

    def _get_product_intercompany_qty_done_dict(
        self, sale_move_lines, purchase_move_lines
    ):
        sale_line = sale_move_lines.move_id.sale_line_id
        sale_bom = self._get_intercompany_kit_bom(
            sale_line.product_id, sale_line.company_id
        )
        if not sale_bom:
            return super()._get_product_intercompany_qty_done_dict(
                sale_move_lines, purchase_move_lines
            )
        # 'sale-kit' situation: N sale moves (components) → 1 po move (kit product)
        # Compute the number of kits delivered
        # from all the component moves, not only the current zip pair.
        kit_qty_sold = sale_line.product_uom._compute_quantity(
            sale_line.product_uom_qty, sale_bom.product_uom_id
        )
        all_sale_moves = self.move_ids.filtered(
            lambda m, sl=sale_line: m.sale_line_id == sl and m.bom_line_id
        )
        kit_qty_done = all_sale_moves._compute_kit_quantities(
            sale_line.product_id, kit_qty_sold, sale_bom, KIT_QUANTITIES_FILTERS
        )
        sale_qty_done = sale_bom.product_uom_id._compute_quantity(
            kit_qty_done, sale_line.product_id.uom_id
        )
        return {purchase_move_lines.product_id: sale_qty_done}

    def _get_intercompany_purchase_pending_moves(self, sale_line, dest_picking):
        """Return the pending moves of the destination picking for the sale line."""
        return sale_line.auto_purchase_line_id.move_ids.filtered(
            lambda x, dp=dest_picking: x.picking_id == dp
            and x.state not in ["done", "cancel"]
        )

    def _is_intercompany_purchase_kit_move(self, move, dest_picking):
        """Return whether the sale move targets a kit on the purchase side."""
        purchase_pending_moves = self._get_intercompany_purchase_pending_moves(
            move.sale_line_id, dest_picking
        )
        return bool(purchase_pending_moves.bom_line_id)
