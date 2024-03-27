# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.sale_purchase_inter_company.tests.test_inter_company_sale_purchase import (
    TestSalePurchaseInterCompany,
)


class TestSalePurchaseStockInterCompany(TestSalePurchaseInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse_b = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_b.id)]
        )

    def test_sale_purchase_stock_inter_company(self):
        self.company_b.warehouse_id = self.warehouse_b
        purchase = self._confirm_so()
        self.assertEqual(purchase.picking_type_id.warehouse_id, self.warehouse_b)
