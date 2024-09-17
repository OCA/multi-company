# Copyright 2024 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_sellers(self, params=False):
        sellers = super()._prepare_sellers(params)
        priority_intercompany_pricelist = (
            self.env.company.priority_intercompany_pricelist_id
        )
        if priority_intercompany_pricelist:
            return sellers.sorted(
                lambda s: (
                    0
                    if s.intercompany_pricelist_id == priority_intercompany_pricelist
                    else 1,
                    s.sequence,
                    -s.min_qty,
                    s.price,
                    s.id,
                )
            )
        return sellers
