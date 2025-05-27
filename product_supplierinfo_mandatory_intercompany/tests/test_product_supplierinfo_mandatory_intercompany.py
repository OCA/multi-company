# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestProductSupplierinfoMandatoryIntercompany(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.legs_attribute = cls.env.ref("product.product_attribute_1")
        cls.legs_att_value_steel = cls.env.ref("product.product_attribute_value_1")
        cls.legs_att_value_alu = cls.env.ref("product.product_attribute_value_2")
        cls.sale_company = cls.env.ref("base.main_company")
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test Pricelist",
                "company_id": cls.sale_company.id,
                "is_intercompany_supplier": True,
            }
        )

        cls.template = cls.env["product.template"].create(
            {
                "name": "Test Product",
                "list_price": 100,
                "categ_id": cls.env.ref("product.product_category_1").id,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.legs_attribute.id,
                            "value_ids": [
                                cls.legs_att_value_steel.id,
                                cls.legs_att_value_alu.id,
                            ],
                        },
                    ),
                ],
            }
        )

        cls.template._create_variant_ids()
        cls.product_with_price = cls.template.product_variant_ids[0]
        cls.product_no_price = cls.template.product_variant_ids[1]

        cls.pricelist_item = cls.env["product.pricelist.item"].create(
            {
                "pricelist_id": cls.pricelist.id,
                "product_tmpl_id": cls.template.id,
                "product_id": cls.product_with_price.id,
                "base": "list_price",
                "fixed_price": 100,
            }
        )

        cls.purchase_company = cls.env.ref(
            "product_supplierinfo_intercompany.purchaser_company"
        )
        cls.partner = cls.env.ref("base.main_partner")
        cls.template.company_id = False
        cls.purchase = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "company_id": cls.purchase_company.id,
            }
        )

        cls.env["purchase.order.line"].create(
            {
                "order_id": cls.purchase.id,
                "product_id": cls.product_with_price.id,
                "product_uom_qty": 1,
                "product_uom": cls.product_with_price.uom_id.id,
            }
        )
        cls.line_no_price = cls.env["purchase.order.line"].create(
            {
                "order_id": cls.purchase.id,
                "product_id": cls.product_no_price.id,
                "product_uom_qty": 1,
                "product_uom": cls.product_no_price.uom_id.id,
            }
        )

    def test_missing_intercompany_supplierinfo_message(self):
        self.assertIn(
            self.product_no_price.display_name,
            self.purchase.missing_inter_supplierinfo_message,
        )
        self.assertNotIn(
            self.product_with_price.display_name,
            self.purchase.missing_inter_supplierinfo_message,
        )

    def test_line_missing_inter_supplierinfo_ids(self):
        self.assertIn(
            self.product_no_price, self.purchase.line_missing_inter_supplierinfo_ids
        )
        self.assertNotIn(
            self.product_with_price, self.purchase.line_missing_inter_supplierinfo_ids
        )

    def test_missing_inter_supplierinfo_button_confirm(self):
        with self.assertRaises(UserError) as m:
            self.purchase.button_confirm()
        self.assertIn(
            "without intercompany supplierinfo",
            m.exception.args[0],
        )
        self.line_no_price.unlink()
        self.purchase.button_confirm()
