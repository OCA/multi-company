# Copyright 2024 Camptocamp SA
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests import common
from odoo.tests.common import Form

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestPartnerMultiCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env["base"].with_context(**DISABLED_MAIL_CONTEXT).env

        group_user = cls.env.ref("base.group_user")
        group_sales_user = cls.env.ref("sales_team.group_sale_salesman")
        group_stock_user = cls.env.ref("stock.group_stock_user")
        group_multi_wh = cls.env.ref("stock.group_stock_multi_warehouses")

        cls.company_sales = cls.env["res.company"].create({"name": "Sales company"})
        cls.company_stock = cls.env["res.company"].create({"name": "Stock company"})
        cls.warehouse_stock = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_stock.id)], limit=1
        )

        cls.user_sales = cls.env["res.users"].create(
            {
                "name": "user company sales with access to company stock",
                "login": "user sales",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            group_user.id,
                            group_sales_user.id,
                            group_multi_wh.id,
                        ],
                    )
                ],
                "company_id": cls.company_sales.id,
                "company_ids": [(6, 0, [cls.company_sales.id, cls.company_stock.id])],
            }
        )
        cls.user_stock = cls.env["res.users"].create(
            {
                "name": "user company stock without access to company sales",
                "login": "user stock",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            group_user.id,
                            group_stock_user.id,
                        ],
                    )
                ],
                "company_id": cls.company_stock.id,
                "company_ids": [(6, 0, [cls.company_sales.id, cls.company_stock.id])],
            }
        )

        cls.partner = cls.env.ref("base.res_partner_12")
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "type": "product", "invoice_policy": "delivery"}
        )
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "location_id": cls.warehouse_stock.wh_output_stock_loc_id.id,
                "product_id": cls.product.id,
                "quantity": 10.0,
            }
        )._apply_inventory()

    def test_sale_stock_warehouse_multicompany(self):
        # Sales user from sales company create and confirm order
        so_env_user_sales = (
            self.env["sale.order"]
            .with_user(self.user_sales)
            .with_context(allowed_company_ids=self.user_sales.company_ids.ids)
        )
        with Form(so_env_user_sales) as order_form:
            order_form.partner_id = self.partner
            order_form.warehouse_id = self.warehouse_stock
            with order_form.order_line.new() as line_form:
                line_form.product_id = self.product
                line_form.product_uom_qty = 1
        order = order_form.save()
        order.action_confirm()
        stock_location = self.warehouse_stock.lot_stock_id
        self.assertEqual(order.picking_ids.location_id, stock_location)

        # Stock user from stock company processes the picking
        picking = order.picking_ids.with_user(self.user_stock).with_context(
            allowed_company_ids=self.user_stock.company_id.ids
        )
        self.env.clear()  # clear cache
        with self.assertRaises(AccessError):
            _ = picking.sale_id.name
        picking.move_ids_without_package.quantity_done = 1.0
        picking.button_validate()

        self.assertEqual(order.order_line.qty_delivered, 1.0)
