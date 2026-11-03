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
