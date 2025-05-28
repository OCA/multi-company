# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _select_seller(
        self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False
    ):
        suppliers = self._get_filtered_sellers(
            partner_id=partner_id,
            quantity=quantity,
            date=date,
            uom_id=uom_id,
            params=params,
        )
        supplier_price_dict = {}
        for supplier in suppliers.filtered(lambda x: x.intercompany_pricelist_id):
            supplier_price_dict[supplier.id] = supplier.price
            supplier.with_context(
                mav_product=self, mav_qty=quantity, automatic_intercompany_sync=True
            )._get_intercompany_price()

        return super()._select_seller(
            partner_id=partner_id,
            quantity=quantity,
            date=date,
            uom_id=uom_id,
            params=params,
        )
