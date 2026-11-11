# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import Command, models


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_intercompany_return_wizard(self, new_picking):
        """Handle kits when returning an intercompany delivery picking (sale side).

        The base implementation matches the purchase return lines to the sale
        return lines by product, which is wrong for kits: the sale and
        purchase sides may have different BOMs and move structures (see
        ``StockPicking._set_intercompany_kit_quantities_done``).

        Recompute the returned kit quantity from the sale return moves, then
        explode it through the purchase BOM so that each purchase return line
        gets its own quantity.
        """
        receipt_moves = self.picking_id.intercompany_picking_id.sudo().move_ids
        if not self._is_intercompany_kit_return(new_picking, receipt_moves):
            return super()._create_intercompany_return_wizard(new_picking)
        return_qty = self._get_purchase_return_quantities(new_picking, receipt_moves)
        return_wizard = self._new_intercompany_return_wizard()
        # Drop the return lines whose purchase line is not part of the sale
        # return.
        purchase_lines = new_picking.move_ids.sale_line_id.auto_purchase_line_id
        exclude_moves = return_wizard.product_return_moves.filtered(
            lambda line: line.move_id.purchase_line_id not in purchase_lines
        )
        return_wizard.product_return_moves = [
            Command.unlink(prm.id) for prm in exclude_moves
        ]
        for po_return_line in return_wizard.product_return_moves:
            move = po_return_line.move_id
            if (
                not move.bom_line_id
                and "lot_id" in po_return_line._fields
                and po_return_line.lot_id
            ):
                quantity = self._get_sale_return_lot_quantity(
                    move.purchase_line_id, po_return_line.lot_id
                )
            else:
                quantity = return_qty[(move.purchase_line_id, move.bom_line_id)]
            po_return_line.write({"quantity": quantity})
        return return_wizard

    def _get_sale_return_lot_quantity(self, purchase_line, lot):
        return sum(
            self.product_return_moves.filtered(
                lambda line: line.move_id.sale_line_id.auto_purchase_line_id
                == purchase_line
                and line.lot_id == lot
            ).mapped("quantity")
        )

    def _is_intercompany_kit_return(self, so_return_picking, receipt_moves):
        purchase_lines = so_return_picking.move_ids.sale_line_id.auto_purchase_line_id
        return bool(
            so_return_picking.move_ids.bom_line_id
            or receipt_moves.filtered(
                lambda m: m.purchase_line_id in purchase_lines
            ).bom_line_id
        )

    def _get_purchase_return_quantities(self, so_return_picking, receipt_moves):
        """Return the quantities to set on the purchase return lines.

        The quantities are keyed by ``(purchase line, BOM line)``, the BOM
        line being empty for the products received as such (kit product
        without purchase BOM, plain products of a mixed return), and
        expressed in the purchased product UoM. Keying by BOM line gives
        each component move the quantity of its own BOM line (important when
        the same product is used on several lines).
        """
        return_qty = defaultdict(float)
        no_bom_line = self.env["mrp.bom.line"]
        for sale_line, sale_return_moves in so_return_picking.move_ids.grouped(
            "sale_line_id"
        ).items():
            if not sale_line:
                continue
            purchase_line = sale_line.auto_purchase_line_id
            receipt_line_moves = receipt_moves.filtered(
                lambda m, pl=purchase_line: m.purchase_line_id == pl
            )
            product = sale_line.product_id
            sale_bom = sale_return_moves._get_intercompany_kit_bom(
                product, sale_line.company_id
            )
            purchase_bom = receipt_line_moves._get_intercompany_kit_bom(
                product, receipt_line_moves.company_id
            )
            if not sale_bom and not purchase_bom:
                # Plain product, not related to a kit: keep the returned
                # quantity as is.
                return_qty[(purchase_line, no_bom_line)] += sum(
                    sale_return_moves.mapped("product_qty")
                )
                continue
            (sale_return_moves | receipt_line_moves)._check_intercompany_kit_tracking()
            kit_qty_returned = sale_return_moves._get_intercompany_kit_qty_done(
                sale_line, sale_bom
            )
            if not purchase_bom:
                return_qty[(purchase_line, no_bom_line)] += kit_qty_returned
                continue
            qty_by_bom_line = purchase_bom._explode_intercompany_kit(
                product, kit_qty_returned
            )
            # The return lines must match the quantities exploded from the BOM
            # of the receipt, otherwise the BOM changed since the receipt.
            receipt_line_moves._check_intercompany_kit_bom_changed(qty_by_bom_line)
            for bom_line, qty in qty_by_bom_line.items():
                return_qty[(purchase_line, bom_line)] += (
                    bom_line.product_uom_id._compute_quantity(
                        qty, bom_line.product_id.uom_id
                    )
                )
        return return_qty
