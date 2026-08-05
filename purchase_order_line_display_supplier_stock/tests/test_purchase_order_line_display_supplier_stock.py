# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import SavepointCase


class TestPurchaseOrderLineDisplaySupplierStock(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_company = cls.env.ref("base.main_company")
        cls.vendor_company = cls.env["res.company"].create({"name": "Vendor Co"})
        cls.vendor_warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.vendor_company.id)], limit=1
        )
        cls.vendor_warehouse.display_stock_on_sol = True
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.vendor_warehouse.lot_stock_id.id,
                "quantity": 30,
            }
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor_company.partner_id.id,
                "company_id": cls.main_company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "name": "Test Product",
                            "product_qty": 1,
                            "product_uom": cls.product.uom_id.id,
                            "date_planned": fields.Datetime.now(),
                            "price_unit": 10,
                        },
                    )
                ],
            }
        )
        cls.line = cls.purchase_order.order_line

    def test_supplier_stock_from_intercompany_supplier(self):
        self.assertIn("30.0", self.line.supplier_stock_info)

    def test_supplier_stock_summed_over_warehouses(self):
        warehouse_2 = self.env["stock.warehouse"].create(
            {
                "name": "Vendor WH2",
                "code": "VWH2",
                "company_id": self.vendor_company.id,
                "display_stock_on_sol": True,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": warehouse_2.lot_stock_id.id,
                "quantity": 12,
            }
        )
        self.assertIn("42.0", self.line.supplier_stock_info)

    def test_no_info_when_supplier_not_a_company(self):
        self.purchase_order.partner_id = self.env.ref("base.res_partner_2")
        self.assertFalse(self.line.supplier_stock_info)
