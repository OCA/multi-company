# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.tests.common import Form

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestSalePartnerCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env["base"].with_context(**DISABLED_MAIL_CONTEXT).env
        cls.company_1 = cls.env["res.company"].create({"name": "Test company 1"})

    def test_sale_partner_company(self):
        partner = self.env.ref("base.res_partner_12")
        partner.sale_company_id = self.company_1

        with Form(self.env["sale.order"]) as order_form:
            order_form.partner_id = partner
        self.order = order_form.save()
        self.assertEqual(self.order.company_id, partner.sale_company_id)

    def test_sale_partner_company_with_default_partner(self):
        partner = self.env.ref("base.res_partner_12")
        partner.sale_company_id = self.company_1
        order_form = Form(
            self.env["sale.order"].with_context(default_partner_id=partner.id)
        )
        self.order = order_form.save()
        self.assertEqual(self.order.company_id, partner.sale_company_id)
