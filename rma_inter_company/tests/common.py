# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form, new_test_user

from odoo.addons.purchase_sale_inter_company.tests import (
    test_inter_company_purchase_sale as test_icps,
)

TestPurchaseSaleInterCompany = test_icps.TestPurchaseSaleInterCompany


class TestRmaInterCompanyBase(TestPurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_rma_inter_company=True))
        cls.intercompany_location = cls.env.ref("stock.stock_location_inter_company")
        cls.warehouse_a = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_a.id)]
        )
        cls.warehouse_a.rma_out_replace_route_id = cls.warehouse_a.rma_out_route_id
        cls.warehouse_b = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_b.id)]
        )
        cls.warehouse_b.rma_out_replace_route_id = cls.warehouse_b.rma_out_route_id
        customer_loc, _supplier_loc = cls.warehouse_a._get_partner_locations()
        cls.customer_loc = customer_loc
        cls.rma_user_a = new_test_user(
            cls.env,
            login="test-rma_user-a",
            groups="rma.rma_group_user_all,stock.group_stock_user,sales_team.group_sale_salesman_all_leads",
            company_id=cls.company_a.id,
            company_ids=[Command.set((cls.company_a).ids)],
        )
        cls.rma_user_b = new_test_user(
            cls.env,
            login="test-rma_user-b",
            groups="rma.rma_group_user_all,stock.group_stock_user,sales_team.group_sale_salesman_all_leads",
            company_id=cls.company_b.id,
            company_ids=[Command.set((cls.company_b).ids)],
        )
        cls.customer = cls.env["res.partner"].create({"name": "Test customer"})
        # In an inter-company context, the drop_shipping route is not required for all
        # companies, only for Company A; therefore, we simulate the manual
        # configuration we would perform
        cls.dropshipping_route = cls.env.ref("stock_dropshipping.route_drop_shipping")
        cls.dropshipping_route.rule_ids.filtered(
            lambda x: x.company_id != cls.company_a
        ).unlink()
        cls.dropshipping_route.company_id = cls.company_a
        cls.stockable_product = cls.env["product.product"].create(
            {
                "name": "Test Stockable Product",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "consu",
                "is_storable": True,
                "route_ids": [
                    Command.link(cls.dropshipping_route.id),
                ],
                "seller_ids": [
                    Command.create(
                        {
                            "partner_id": cls.company_b.partner_id.id,
                            "company_id": cls.company_a.id,
                        }
                    ),
                ],
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Test product 2",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls._update_available_quantity(cls.product, cls.warehouse_b.lot_stock_id, 1)
        # Create SO Company A
        order_form = Form(cls.env["sale.order"].with_company(cls.company_a))
        order_form.partner_id = cls.customer
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product
        cls.so_a = order_form.save()
        cls.operation = cls.env.ref("rma.rma_operation_replace")

    @classmethod
    def _update_available_quantity(self, product, location, qty):
        self.env["stock.quant"]._update_available_quantity(product, location, qty)

    def _create_rma(self, order, user):
        order = order.with_context(allowed_company_ids=user.company_ids.ids)
        action_res = order.with_user(user).action_create_rma()
        wizard_form = Form(
            self.env[action_res["res_model"]]
            .browse(action_res["res_id"])
            .with_user(user)
        )
        wizard_form.operation_id = self.operation
        wizard = wizard_form.save()
        res = wizard.create_and_open_rma()
        return self.env[res["res_model"]].browse(res["res_id"])
