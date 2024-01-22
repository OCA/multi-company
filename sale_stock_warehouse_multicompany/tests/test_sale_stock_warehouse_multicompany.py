# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.tests.common import Form

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestPartnerMultiCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env["base"].with_context(**DISABLED_MAIL_CONTEXT).env

        cls.company_1 = cls.env["res.company"].create({"name": "Test company 1"})
        cls.company_2 = cls.env["res.company"].create({"name": "Test company 2"})
        cls.warehouse_1 = cls.env["stock.warehouse"].create(
            {
                "name": "Base Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "ship_only",
                "code": "BWH",
                "company_ids": [(6, 0, (cls.company_2 + cls.company_1).ids)],
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "type": "product", "invoice_policy": "delivery"}
        )
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "location_id": cls.warehouse_1.wh_output_stock_loc_id.id,
                "product_id": cls.product.id,
                "quantity": 10.0,
            }
        )._apply_inventory()

    def test_sale_stock_warehouse_multicompany(self):
        self.env.user.company_id = self.company_2

        # Test company 2 create and confirm order
        with Form(self.env["sale.order"]) as order_form:
            order_form.partner_id = self.env.ref("base.res_partner_12")
            order_form.warehouse_id = self.warehouse_1
            with order_form.order_line.new() as line_form:
                line_form.product_id = self.product
                line_form.product_uom_qty = 1
        self.order = order_form.save()
        self.order.action_confirm()

        # Test company 1 process logitic steps from warehouse_1
        self.env.user.company_id = self.company_1
        stock_location = self.warehouse_1.lot_stock_id
        self.assertEqual(self.order.picking_ids.location_id, stock_location)
        # Process picking
        self.order.picking_ids.move_ids_without_package.quantity_done = 1.0
        self.order.picking_ids.button_validate()

        self.assertEqual(self.order.order_line.qty_delivered, 1.0)
