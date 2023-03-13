# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.purchase_sale_inter_company.tests.test_inter_company_purchase_sale import (
    TestPurchaseSaleInterCompany,
)

class TestPurchaseSaleLotIntercompany(TestPurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.lot_test = cls.env["stock.production.lot"].create(
            {
                "name": "lot_test",
                "product_id": cls.product.id,
                "company_id": cls.warehouse_a.company_id.id,
            }
        )
        cls.purchase_company_a.order_line[0].lot_id = cls.lot_test

    def test_with_propagated_serial_number(self):
        self.company_b.so_from_po = True
        sale = self._approve_po()
        self.assertEqual(sale.order_line[0].lot_id,self.lot_test)

    def test_without_propagated_serial_number(self):
        sale = self._approve_po()
        self.assertFalse(sale.order_line[0].lot_id)
