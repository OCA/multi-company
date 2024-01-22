# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form

from odoo.addons.purchase_sale_inter_company.tests.test_inter_company_purchase_sale import (
    TestPurchaseSaleInterCompany,
)


class TestPurchaseSaleStockInterCompanyMrp(TestPurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create Kit and Components
        cls.kit_product = cls.env["product.product"].create(
            {
                "name": "Kit Product",
                "type": "consu",
            }
        )
        cls.component_1 = cls.env["product.product"].create(
            {
                "name": "Component 1",
                "type": "product",
            }
        )
        cls.component_2 = cls.env["product.product"].create(
            {
                "name": "Component 2",
                "type": "product",
            }
        )
        cls.partner_company_a.company_id = False
        cls.partner_company_b.company_id = False
        # Create BoM
        bom = Form(cls.env["mrp.bom"])
        bom.company_id = cls.company_b
        bom.product_id = cls.kit_product
        bom.product_tmpl_id = cls.kit_product.product_tmpl_id
        bom.type = "phantom"
        with bom.bom_line_ids.new() as line_form:
            line_form.product_id = cls.component_1
            line_form.product_qty = 1.0
        with bom.bom_line_ids.new() as line_form:
            line_form.product_id = cls.component_2
            line_form.product_qty = 3.0
        cls.bom = bom.save()
        # Create PO
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = cls.partner_company_b
        with po.order_line.new() as line_form:
            line_form.product_id = cls.kit_product
            line_form.product_qty = 3.0
            line_form.price_unit = 450.0
        cls.kit_po = po.save()

    def test_purchase_sale_stock_inter_company_mrp_sale_kit(self):
        self.kit_po.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.kit_po.id)])
        )
        sale_picking = sale.picking_ids[0]
        self.assertEqual(len(sale_picking.move_ids), 2)
        component_1_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        component_2_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_2
        )
        component_1_move.write({"quantity_done": 3.0})
        component_2_move.write({"quantity_done": 9.0})
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 1)
        self.assertEqual(purchase_picking.move_ids.quantity_done, 3.0)

    def test_purchase_sale_stock_inter_company_mrp_sale_kit_partial(self):
        self.kit_po.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.kit_po.id)])
        )
        sale_picking = sale.picking_ids[0]
        self.assertEqual(len(sale_picking.move_ids), 2)
        component_1_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        component_2_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_2
        )
        # Deliver only 2 kits
        component_1_move.write({"quantity_done": 2.0})
        component_2_move.write({"quantity_done": 6.0})
        sale_picking.with_context(skip_backorder=True).button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 1)
        self.assertEqual(purchase_picking.move_ids.quantity_done, 2.0)

    def test_purchase_sale_stock_inter_company_mrp_purchase_kit(self):
        self.bom.write({"company_id": self.company_a.id})
        self.kit_po.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.kit_po.id)])
        )
        sale_picking = sale.picking_ids[0]
        self.assertEqual(len(sale_picking.move_ids), 1)
        sale_picking.move_ids.write({"quantity_done": 3.0})
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 2)
        component_1_move = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        component_2_move = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_2
        )
        self.assertEqual(component_1_move.quantity_done, 3.0)
        self.assertEqual(component_2_move.quantity_done, 9.0)

    def test_purchase_sale_stock_inter_company_mrp_purchase_kit_partial(self):
        self.bom.write({"company_id": self.company_a.id})
        self.kit_po.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.kit_po.id)])
        )
        sale_picking = sale.picking_ids[0]
        self.assertEqual(len(sale_picking.move_ids), 1)
        # Deliver only 2 kits
        sale_picking.move_ids.write({"quantity_done": 2.0})
        sale_picking.with_context(skip_backorder=True).button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 2)
        component_1_move = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        component_2_move = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_2
        )
        self.assertEqual(component_1_move.quantity_done, 2.0)
        self.assertEqual(component_2_move.quantity_done, 6.0)

    def test_purchase_sale_stock_inter_company_mrp_sale_purchase_kit(self):
        # Create a different BoM for Company A
        self.component_3 = self.env["product.product"].create(
            {
                "name": "Component 3",
                "type": "product",
            }
        )
        bom = Form(self.env["mrp.bom"])
        bom.company_id = self.company_a
        bom.product_id = self.kit_product
        bom.product_tmpl_id = self.kit_product.product_tmpl_id
        bom.type = "phantom"
        with bom.bom_line_ids.new() as line_form:
            line_form.product_id = self.component_1
            line_form.product_qty = 1.0
        with bom.bom_line_ids.new() as line_form:
            line_form.product_id = self.component_2
            line_form.product_qty = 2.0
        with bom.bom_line_ids.new() as line_form:
            line_form.product_id = self.component_3
            line_form.product_qty = 5.0
        bom.save()
        self.kit_po.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.kit_po.id)])
        )
        sale_picking = sale.picking_ids[0]
        self.assertEqual(len(sale_picking.move_ids), 2)
        component_1_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        component_2_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_2
        )
        component_1_move.write({"quantity_done": 3.0})
        component_2_move.write({"quantity_done": 9.0})
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 3)
        component_1_move = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        component_2_move = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_2
        )
        component_3_move = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_3
        )
        self.assertEqual(component_1_move.quantity_done, 3.0)
        self.assertEqual(component_2_move.quantity_done, 6.0)
        self.assertEqual(component_3_move.quantity_done, 15.0)
