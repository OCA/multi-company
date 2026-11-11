# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

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
        kit_moves = super()._set_intercompany_kit_quantities_done(
            purchase, dest_picking
        )
        for sale_line, sale_moves in self.move_ids.grouped("sale_line_id").items():
            purchase_moves = self._get_intercompany_purchase_pending_moves(
                sale_line, dest_picking
            )
            if not purchase_moves:
                continue
            purchase_line = sale_line.auto_purchase_line_id
            product = sale_line.product_id
            sale_bom = sale_line.move_ids._get_intercompany_kit_bom(
                product, sale_line.company_id
            )
            purchase_bom = purchase_line.move_ids._get_intercompany_kit_bom(
                product, purchase.company_id
            )
            if not sale_bom and not purchase_bom:
                continue
            (sale_moves | purchase_moves)._check_intercompany_kit_tracking()
            kit_qty_delivered = sale_line.move_ids._get_intercompany_kit_qty_delivered(
                sale_line, sale_bom
            )
            if purchase_bom:
                qty_by_bom_line = purchase_bom._explode_intercompany_kit(
                    product, kit_qty_delivered
                )
            else:
                qty_by_bom_line = {self.env["mrp.bom.line"]: kit_qty_delivered}
            qty_received_by_bom_line = (
                purchase_line.move_ids._get_intercompany_qty_received_by_bom_line()
            )
            sign = -1 if self._is_intercompany_return_reception() else 1
            for bom_line, moves in purchase_moves.grouped("bom_line_id").items():
                moves._set_intercompany_qty_done(
                    sign
                    * (
                        qty_by_bom_line[bom_line]
                        - qty_received_by_bom_line.get(bom_line, 0.0)
                    )
                )
            kit_moves |= sale_moves
        return kit_moves

    def _get_intercompany_purchase_pending_moves(self, sale_line, dest_picking):
        """Return the pending moves of the destination picking for the sale line."""
        return sale_line.auto_purchase_line_id.move_ids.filtered(
            lambda x, dp=dest_picking: x.picking_id == dp
            and x.state not in ["done", "cancel"]
        )
