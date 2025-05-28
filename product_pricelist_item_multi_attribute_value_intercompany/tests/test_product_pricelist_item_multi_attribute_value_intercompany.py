# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.product_pricelist_item_multi_attribute_value.tests.common import (
    CommonPricelistPerMultiAttributeValue,
)


class TestProductPricelistItemMultiAttributeValueIntercompany(
    CommonPricelistPerMultiAttributeValue
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.sale_company = cls.env.ref("base.main_company")
        cls.purchase_company = cls.env.ref(
            "product_supplierinfo_intercompany.purchaser_company"
        )
        cls.partner = cls.env.ref("base.main_partner")

        cls.pricelist.write(
            {
                "company_id": cls.sale_company.id,
                "is_intercompany_supplier": True,
            }
        )
        cls.template.company_id = False

        cls.purchase = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "company_id": cls.purchase_company.id,
            }
        )

    def new_purchase_line(self, product):
        return self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase.id,
                "product_id": product.id,
                "product_uom_qty": 1,
                "product_uom": product.uom_id.id,
            }
        )

    def test_product_alu_black(self):
        pol = self.new_purchase_line(self.product_alu_black)
        self.assertEqual(pol.price_unit, 175)

    def test_product_steel_white(self):
        pol = self.new_purchase_line(self.product_steel_white)
        self.assertEqual(pol.price_unit, 150)

    def test_product_alu_white(self):
        pol = self.new_purchase_line(self.product_alu_white)
        self.assertEqual(pol.price_unit, 175)

    def test_product_steel_white_no_additional_price(self):
        self.color_price.unlink()
        pol = self.new_purchase_line(self.product_steel_white)
        self.assertEqual(pol.price_unit, 100)

    def test_product_steel_white_confirm_purchase(self):
        pol = self.new_purchase_line(self.product_steel_white)
        self.color_price.write({"additional_price": 1000})
        self.purchase.button_confirm()
        self.assertEqual(pol.price_unit, 150)
        # simulate an intercompany sale from purchase
        self.new_sale_line(self.product_steel_white)
        self.sale.auto_purchase_order_id = self.purchase
        self.sale.order_line.auto_purchase_line_id = pol
        self.sale.action_confirm()
        self.assertEqual(pol.price_unit, 1100)
