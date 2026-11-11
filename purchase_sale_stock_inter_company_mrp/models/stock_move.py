# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError

# The moves passed to _compute_kit_quantities are the moves of the sale
# picking: only the cancelled ones are excluded, nothing to subtract.
KIT_QUANTITIES_FILTERS = {
    "incoming_moves": lambda m: m.state != "cancel",
    "outgoing_moves": lambda m: False,
}


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_intercompany_kit_bom(self, product, company):
        """Return the phantom BOM of the kit moved by these moves.

        The BOM is resolved from the product because with nested phantom
        BOMs the component moves point to a sub-BOM through their
        ``bom_line_id``, while the sync needs the top-level kit BOM.
        """
        if not self.bom_line_id:
            return self.env["mrp.bom"]
        bom = self.env["mrp.bom"]._bom_find(
            product, company_id=company.id, bom_type="phantom"
        )[product]
        if not bom:
            self._raise_intercompany_kit_bom_changed(self.product_id)
        return bom

    def _get_intercompany_kit_qty_done(self, sale_line, sale_bom):
        if not sale_bom:
            return sum(
                self.filtered(lambda m: m.state != "cancel").mapped(
                    lambda m: m.product_uom._compute_quantity(
                        m.quantity, m.product_id.uom_id
                    )
                    if m.picked
                    else m.product_qty
                )
            )
        kit_qty_sold = sale_line.product_uom._compute_quantity(
            sale_line.product_uom_qty, sale_bom.product_uom_id
        )
        kit_qty_done = self._compute_kit_quantities(
            sale_line.product_id, kit_qty_sold, sale_bom, KIT_QUANTITIES_FILTERS
        )
        return sale_bom.product_uom_id._compute_quantity(
            kit_qty_done, sale_line.product_id.uom_id
        )

    def _check_intercompany_kit_tracking(self):
        """Reject tracked products: their lots cannot be synchronized.

        The moves are the products moved on either side of the kit, so this
        also covers the products of nested phantom BOMs. Their lots belong to
        the moved products, while the other company may move another product
        or decompose it with another BOM, so there is no reliable lot mapping.
        """
        tracked_products = self.product_id.filtered(
            lambda product: product.tracking != "none"
        )
        if tracked_products:
            raise UserError(
                self.env._(
                    "Inter-company kit synchronization does not support "
                    "tracked products: %(products)s",
                    products=", ".join(tracked_products.mapped("display_name")),
                )
            )

    def _check_intercompany_kit_bom_changed(self, bom_lines):
        """Check the moves still match the BOM lines of the computed quantities.

        Each move's BOM line must be in ``bom_lines`` and each consumable BOM
        line in ``bom_lines`` must be in the move's BOM lines, otherwise the
        BOM changed since the receipt.
        """
        bom_line_ids = {
            line.id for line in bom_lines if line.product_id.type == "consu"
        }
        moves = self.filtered("bom_line_id")
        move_bom_line_ids = set(moves.bom_line_id.ids)
        if bom_line_ids == move_bom_line_ids:
            return
        stale_moves = moves.filtered(lambda m: m.bom_line_id.id not in bom_line_ids)
        missing_lines = self.env["mrp.bom.line"].browse(
            bom_line_ids - move_bom_line_ids
        )
        self._raise_intercompany_kit_bom_changed(
            stale_moves.product_id | missing_lines.product_id
        )

    def _raise_intercompany_kit_bom_changed(self, products):
        raise UserError(
            self.env._(
                "The kit BOM changed since the receipt creation: the quantities "
                "cannot be synchronized for %(products)s",
                products=", ".join(products.mapped("display_name")),
            )
        )
