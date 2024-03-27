# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import Form, common

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestSaleProductCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env["base"].with_context(**DISABLED_MAIL_CONTEXT).env

    def test_onchange_product_company_sale_ok_companies(self):
        company1 = self.env["res.company"].create({"name": "Test Company 1"})
        company2 = self.env["res.company"].create({"name": "Test Company 2"})
        product = self.env["product.template"].create({"name": "Test Product"})
        product.sale_ok_company_ids = [(6, 0, [company1.id, company2.id])]
        with Form(product) as product_form:
            product_form.company_id = company2
        product = product_form.save()
        self.assertEqual(product.sale_ok_company_ids, company2)

    def test_sale_product_company(self):
        result = self.env["sale.order"].get_view(
            self.env.ref("sale.view_order_form").id,
            "form",
        )
        doc = etree.XML(result["arch"])
        field = doc.xpath("//field[@name='product_template_id']")
        domain = field[0].get("domain")
        self.assertTrue(
            "'|', ('sale_ok_company_ids', 'in', parent.company_id), "
            "('sale_ok_company_ids', '=', False)" in domain
        )
