# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    def _get_inter_company_lot_product(self, **kwargs):
        """Return the product to use when searching/creating the lot.
        Hook for customization. By default, it’s just the selling company
        lot’s product.
        """
        self.ensure_one()
        return self.product_id

    def prepare_inter_company_lot_values(self, company, product):
        res = {
            "name": self.name,
            "product_id": product.id,
            "company_id": company.id,
        }
        if "expiration_date" in self._fields:
            res.update(expiration_date=self.expiration_date)
        return res

    def get_inter_company_lot(self, company, **kwargs):
        self.ensure_one()
        product = self._get_inter_company_lot_product(**kwargs)
        lot = self.sudo().search(
            [
                ("name", "=", self.name),
                ("product_id", "=", product.id),
                ("company_id", "=", company.id),
            ]
        )
        if not lot:
            lot = self.sudo().create(
                self.prepare_inter_company_lot_values(company, product)
            )
        return lot
