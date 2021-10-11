# Copyright 2021 Acsone SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import SavepointCase


class TestDeliveryState(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_demo = cls.env.ref("base.user_demo")
        company_obj = cls.env["res.company"]
        cls.company1 = company_obj.create({"name": "Company 1"})
        cls.company2 = company_obj.create({"name": "Company 2"})

        cls.product_shipping_cost = (
            cls.env["product.product"]
            .with_company(cls.company1)
            .create(
                {
                    "type": "service",
                    "name": "Shipping costs",
                    "standard_price": 10,
                    "list_price": 100,
                }
            )
        )

        cls.product_shipping_cost2 = (
            cls.env["product.product"]
            .with_company(cls.company2)
            .create(
                {
                    "type": "service",
                    "name": "Shipping costs",
                    "standard_price": 10,
                    "list_price": 100,
                }
            )
        )

        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "fixed_price": 99.99,
                "product_id": cls.product_shipping_cost.id,
            }
        )

        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.partner_shipping = cls.env["res.partner"].create(
            {"name": "Mr. Odoo (shipping)"}
        )
        cls.product = (
            cls.env["product.product"]
            .with_company(cls.company1)
            .create({"name": "Test product", "type": "product"})
        )
        cls.product2 = (
            cls.env["product.product"]
            .with_company(cls.company2)
            .create({"name": "Test product", "type": "product"})
        )

        cls.sale = (
            cls.env["sale.order"]
            .with_company(cls.company1)
            .create(
                {
                    "partner_id": cls.partner.id,
                    "partner_shipping_id": cls.partner_shipping.id,
                    "pricelist_id": cls.pricelist.id,
                    "order_line": [
                        (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                    ],
                }
            )
        )
        cls.sale2 = (
            cls.env["sale.order"]
            .with_company(cls.company2)
            .create(
                {
                    "partner_id": cls.partner.id,
                    "partner_shipping_id": cls.partner_shipping.id,
                    "pricelist_id": cls.pricelist.id,
                    "order_line": [
                        (0, 0, {"product_id": cls.product2.id, "product_uom_qty": 1})
                    ],
                }
            )
        )

    def test_carrier(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": self.sale.id, "default_carrier_id": self.carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()

    def test_carrier2(self):

        carrier2 = self.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "fixed_price": 99.99,
                "product_id": self.product_shipping_cost2.id,
            }
        )

        self.assertEqual(carrier2.company_id.id, self.company2.id)

        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": self.sale.id, "default_carrier_id": carrier2}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        with self.assertRaises(UserError):
            choose_delivery_carrier.button_confirm()

        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": self.sale2.id, "default_carrier_id": carrier2}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
