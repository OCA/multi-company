# Copyright (c) 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.sale_purchase_stock_inter_company.tests.test_inter_company_sale_purchase_stock import (  # noqa: B950
    TestSalePurchaseStockInterCompanyBase,
)


class TestSalePurchaseLotInterCompanyBase(TestSalePurchaseStockInterCompanyBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.lot_test = cls.env["stock.lot"].create(
            {
                "name": "lot_test",
                "product_id": cls.product.id,
                "company_id": cls.warehouse_b.company_id.id,
            }
        )
        cls.sale_company_a.order_line[0].lot_id = cls.lot_test


class TestSalePurchaseLotInterCompany(TestSalePurchaseLotInterCompanyBase):
    def test_with_propagated_serial_number_so_po(self):
        self.company_b.propagated_serial_number_so_po = True
        purchase = self._confirm_so()
        self.assertEqual(purchase.order_line[0].lot_id.name, "lot_test")

    def test_without_propagated_serial_number_so_po(self):
        purchase = self._confirm_so()
        self.assertFalse(purchase.order_line[0].lot_id)
