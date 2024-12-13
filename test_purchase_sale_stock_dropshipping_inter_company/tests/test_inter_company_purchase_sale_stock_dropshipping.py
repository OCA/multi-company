#  Copyright (c) 2024 Groupe Voltaire
#  @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import Form

from odoo.addons.purchase_sale_inter_company.tests.test_inter_company_purchase_sale import (
    TestPurchaseSaleInterCompanyBase,
)


class TestPurchaseSaleStockDropShippingInterCompany(TestPurchaseSaleInterCompanyBase):
    def test_purchase_sale_stock_drop_shipping_inter_company(self):
        self.external_supplier = self.env["res.partner"].create({"name": "Supplier"})
        self.external_customer = self.env["res.partner"].create({"name": "Customer"})
        self.dropship_route = self.env.ref("stock_dropshipping.route_drop_shipping")
        self.dropship_product = self.env["product.product"].create(
            [
                {
                    "name": "Dropship product",
                    "type": "product",
                    "route_ids": [Command.link(self.dropship_route.id)],
                    "seller_ids": [
                        Command.create(
                            {
                                "partner_id": self.partner_company_b.id,
                                "min_qty": 0,
                                "delay": 5,
                                "company_id": self.company_a.id,
                            }
                        ),
                        Command.create(
                            {
                                "partner_id": self.external_supplier.id,
                                "min_qty": 5,
                                "delay": 1,
                                "company_id": self.company_b.id,
                            }
                        ),
                    ],
                }
            ]
        )

        original_sale_form = Form(
            self.env["sale.order"]
            .with_company(self.company_a)
            .with_user(self.user_company_a)
        )
        original_sale_form.partner_id = self.external_customer

        with original_sale_form.order_line.new() as line_form:
            line_form.product_id = self.dropship_product
            line_form.product_uom_qty = 5.0
            line_form.price_unit = 100.0
        original_sale = original_sale_form.save()

        original_sale.action_confirm()
        inter_company_po = original_sale._get_purchase_orders()
        inter_company_po.button_confirm()
        inter_company_so = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", inter_company_po.id)])
        )
        external_po = inter_company_so._get_purchase_orders()
        external_po.button_confirm()
        external_po.picking_ids.move_ids.quantity_done = 3.0
        backorder_wizard_dict = external_po.picking_ids.button_validate()
        backorder_wizard = Form(
            self.env[backorder_wizard_dict["res_model"]].with_context(
                **backorder_wizard_dict["context"]
            )
        ).save()
        backorder_wizard.process()
        self.assertEqual(inter_company_so.order_line.qty_delivered, 3.0)
        self.assertEqual(original_sale.order_line.qty_delivered, 3.0)
        backorder = external_po.picking_ids.backorder_ids
        backorder.move_ids.quantity_done = backorder.move_ids.product_qty
        backorder.button_validate()
        self.assertEqual(
            inter_company_so.order_line.qty_delivered,
            inter_company_so.order_line.product_uom_qty,
        )
        self.assertEqual(
            original_sale.order_line.qty_delivered,
            original_sale.order_line.product_uom_qty,
        )
