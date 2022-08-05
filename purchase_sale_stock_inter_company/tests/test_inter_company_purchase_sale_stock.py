# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.purchase_sale_inter_company.tests.test_inter_company_purchase_sale import (
    TestPurchaseSaleInterCompany,
)


class TestPurchaseSaleStockInterCompany(TestPurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StockLocation = cls.env["stock.location"]
        cls.StockWarehouse = cls.env["stock.warehouse"]
        cls.location_stock_company_a = cls.StockLocation.create(
            {"name": "Stock - a", "usage": "internal", "company_id": cls.company_a.id}
        )
        cls.location_output_company_a = cls.StockLocation.create(
            {"name": "Output - a", "usage": "internal", "company_id": cls.company_a.id}
        )
        cls.warehouse_company_a = cls.StockWarehouse.create(
            {
                "name": "purchase warehouse - a",
                "code": "CMPa",
                "wh_input_stock_loc_id": cls.location_stock_company_a.id,
                "lot_stock_id": cls.location_stock_company_a.id,
                "wh_output_stock_loc_id": cls.location_output_company_a.id,
                "partner_id": cls.partner_company_a.id,
                "company_id": cls.company_a.id,
            }
        )
        cls.location_stock_company_b = cls.StockLocation.create(
            {"name": "Stock - b", "usage": "internal", "company_id": cls.company_b.id}
        )
        cls.location_output_company_b = cls.StockLocation.create(
            {"name": "Output - b", "usage": "internal", "company_id": cls.company_b.id}
        )
        cls.warehouse_company_b = cls.StockWarehouse.create(
            {
                "name": "purchase warehouse - b",
                "code": "CMPb",
                "wh_input_stock_loc_id": cls.location_stock_company_b.id,
                "lot_stock_id": cls.location_stock_company_b.id,
                "wh_output_stock_loc_id": cls.location_output_company_b.id,
                "partner_id": cls.partner_company_b.id,
                "company_id": cls.company_b.id,
            }
        )
        cls.company_a.warehouse_id = cls.warehouse_company_a
        cls.company_b.warehouse_id = cls.warehouse_company_b

    def test_purchase_sale_stock_inter_company(self):
        self.purchase_company_a.notes = "Test note"
        # Confirm the purchase of company A
        self.purchase_company_a.with_user(self.user_company_a).button_approve()
        # Check sale order created in company B
        sales = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.purchase_company_a.id)])
        )
        self.assertEqual(
            sales.partner_shipping_id,
            self.purchase_company_a.picking_type_id.warehouse_id.partner_id,
        )
        warehouse_b = self.StockWarehouse.search([("name", "=", "Company B")])
        self.assertEqual(sales.warehouse_id, warehouse_b)
