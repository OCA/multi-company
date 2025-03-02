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
    def _create_warehouse(cls, code, company):
        address = cls.env["res.partner"].create({"name": f"{code} address"})
        return cls.env["stock.warehouse"].create(
            {
                "name": f"Warehouse {code}",
                "code": code,
                "partner_id": address.id,
                "company_id": company.id,
            }
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configure 2 Warehouse per company
        cls.warehouse_a = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_a.id)]
        )
        cls.warehouse_b = cls._create_warehouse("CA-WB", cls.company_a)

        cls.warehouse_c = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_b.id)]
        )
        cls.warehouse_d = cls._create_warehouse("CB-WD", cls.company_b)
        cls.company_b.warehouse_id = cls.warehouse_c

    def test_deliver_to_warehouse_a(self):
        self.purchase_company_a.picking_type_id = self.warehouse_a.in_type_id
        sale = self._approve_po()
        self.assertEqual(self.warehouse_a.partner_id, sale.partner_shipping_id)

    def test_deliver_to_warehouse_b(self):
        self.purchase_company_a.picking_type_id = self.warehouse_b.in_type_id
        sale = self._approve_po()
        self.assertEqual(self.warehouse_b.partner_id, sale.partner_shipping_id)

    def test_send_from_warehouse_c(self):
        self.company_b.warehouse_id = self.warehouse_c
        sale = self._approve_po()
        self.assertEqual(sale.warehouse_id, self.warehouse_c)

    def test_send_from_warehouse_d(self):
        self.company_b.warehouse_id = self.warehouse_d
        sale = self._approve_po()
        self.assertEqual(sale.warehouse_id, self.warehouse_d)

    def test_purchase_sale_stock_inter_company(self):
        self.purchase_company_a.notes = "Test note"
        sale = self._approve_po()
        self.assertEqual(
            sale.partner_shipping_id,
            self.purchase_company_a.picking_type_id.warehouse_id.partner_id,
        )
        self.assertEqual(sale.warehouse_id, self.warehouse_c)

    def test_sync_intercompany_picking_qty_with_backorder(self):
        self.product.type = "product"
        self.partner_company_b.company_id = False
        purchase = self.purchase_company_a
        sale = self._approve_po()
        sale.action_confirm()
        sale_picking = sale.picking_ids[0]
        sale_picking.sudo().action_confirm()
        sale_picking.move_ids.quantity_done = 1.0
        res_dict = sale_picking.sudo().button_validate()
        self.env["stock.backorder.confirmation"].with_context(
            **res_dict["context"]
        ).process()
        sale_picking2 = sale.picking_ids.filtered(lambda p: p.state != "done")
        self.assertEqual(purchase.picking_ids[0].move_line_ids.qty_done, 1)
        self.assertEqual(purchase.picking_ids[1].move_line_ids.qty_done, 0)
        self.assertEqual(purchase.order_line.qty_received, 1)
        sale_picking2.move_ids.quantity_done = 2.0
        sale_picking2.sudo().action_confirm()
        sale_picking2.sudo().button_validate()
        self.assertEqual(purchase.picking_ids[0].move_line_ids.qty_done, 1)
        self.assertEqual(purchase.picking_ids[1].move_line_ids.qty_done, 2)
        self.assertEqual(purchase.order_line.qty_received, 3)
