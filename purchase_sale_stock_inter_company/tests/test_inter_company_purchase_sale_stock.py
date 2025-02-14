# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import Form

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
    def _create_purchase_order_with_product(cls, partner):
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        cls.product_a.invoice_policy = "order"

        with po.order_line.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.product_qty = 280
        return po.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={"test_queue_job_no_delay": 1})
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
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )
        # Configure User
        cls.user_company_a.groups_id += cls.env.ref("stock.group_stock_user")
        cls._configure_user(cls.user_company_a)
        cls._configure_user(cls.user_company_b)

        # Configure Company B (the supplier)
        cls.company_b.so_from_po = True
        cls.company_b.sale_auto_validation = 1

        cls.intercompany_sale_user_id.company_ids |= cls.company_a
        cls.company_b.intercompany_sale_user_id = cls.intercompany_sale_user_id
        companies = cls.env["res.company"].search([])
        companies.write({"link_purchase_sale_picking": True})

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

    def test_purchase_sale_stock_inter_company_without_linking_pickings(self):
        self.company_b.link_purchase_sale_picking = False
        self.partner_company_b.company_id = self.company_a
        purchase = self._create_purchase_order_with_product(self.partner_company_b)
        purchase.with_user(self.user_company_a).sudo().button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", purchase.id)])
        )
        sale.action_confirm()
        self.assertEqual(
            sale.partner_shipping_id,
            purchase.picking_type_id.warehouse_id.partner_id,
        )
        self.assertEqual(sale.warehouse_id, self.warehouse_c)
        purchase_picking_id = purchase.picking_ids
        sale_picking_id = sale.picking_ids
        for move_id in sale_picking_id.move_ids:
            move_id.quantity_done = move_id.product_uom_qty
        sale_picking_id._action_done()
        self.assertEqual(purchase_picking_id.state, "assigned")
        self.assertEqual(sale_picking_id.state, "done")

    def test_purchase_sale_stock_inter_company_linking_pickings(self):
        self.partner_company_b.company_id = self.company_a
        purchase = self._create_purchase_order_with_product(self.partner_company_b)
        purchase.with_user(self.user_company_a).sudo().button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", purchase.id)])
        )
        sale.action_confirm()
        self.assertEqual(
            sale.partner_shipping_id,
            purchase.picking_type_id.warehouse_id.partner_id,
        )
        self.assertEqual(sale.warehouse_id, self.warehouse_c)
        purchase_picking_id = purchase.picking_ids
        sale_picking_id = sale.picking_ids
        for move_id in sale_picking_id.move_ids:
            move_id.quantity_done = move_id.product_uom_qty
        sale_picking_id._action_done()
        self.assertEqual(purchase_picking_id.state, "done")
        self.assertEqual(sale_picking_id.state, "done")

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
