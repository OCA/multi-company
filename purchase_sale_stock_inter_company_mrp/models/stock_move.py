# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

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

    def _check_intercompany_kit_bom_changed(self, qty_by_bom_line):
        """Check the moves still match the BOM lines of the computed quantities.

        ``qty_by_bom_line`` maps the BOM lines of the current BOM to their
        quantity. Each move's BOM line must be in ``qty_by_bom_line`` and
        each BOM line in ``qty_by_bom_line`` must be in the move's BOM lines,
        otherwise the BOM changed since the receipt.
        """
        bom_line_ids = {line.id for line in qty_by_bom_line if line}
        moves = self.filtered("bom_line_id")
        move_bom_line_ids = set(moves.bom_line_id.ids)
        if bom_line_ids == move_bom_line_ids:
            return
        stale_moves = moves.filtered(lambda m: m.bom_line_id.id not in bom_line_ids)
        missing_lines = self.env["mrp.bom.line"].browse(
            bom_line_ids - move_bom_line_ids
        )
        products = stale_moves.product_id | missing_lines.product_id
        raise UserError(
            self.env._(
                "The kit BOM changed since the receipt creation: the quantities "
                "cannot be synchronized for %(products)s",
                products=", ".join(products.mapped("display_name")),
            )
        )
