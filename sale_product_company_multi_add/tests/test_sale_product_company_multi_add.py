# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import Form, common

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestSaleProductCompanyMultiAdd(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env["base"].with_context(**DISABLED_MAIL_CONTEXT).env
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def test_sale_import_product_wizard_sale_company(self):
        so = self.env["sale.order"].create({"partner_id": self.partner.id})
        wizard = Form(
            self.env["sale.import.products"].with_context(
                active_id=so.id, active_model="sale.order"
            )
        ).save()

        self.assertEqual(wizard.sale_company_id, so.company_id)

    def test_sale_product_company(self):
        result = self.env["sale.order"].get_view(
            self.env.ref("sale_product_multi_add.view_import_product_to_sale").id,
            "form",
        )
        doc = etree.XML(result["arch"])
        field = doc.xpath("//field[@name='products']")
        domain = field[0].get("domain")
        self.assertTrue(
            "('sale_ok', '=', True), '|', ('sale_ok_company_ids', 'in', sale_company_id), "
            "('sale_ok_company_ids', '=', False)" in domain
        )
