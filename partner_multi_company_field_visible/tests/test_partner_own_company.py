# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPartnerOwnCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, test_multi_company_field_visible=True)
        )
        cls.company_a = cls.env["res.company"].create({"name": "FV Partner A"})
        cls.company_b = cls.env["res.company"].create({"name": "FV Partner B"})
        cls.merchant_a = new_test_user(
            cls.env,
            login="fv_partner_merchant_a",
            groups="base.group_user,base.group_partner_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.Partner = cls.env["res.partner"]

    def test_partner_compute_and_merge(self):
        # Set company_ids after create so partner_company_default's create-time
        # default does not override our shared A+B scenario.
        partner = self.Partner.create({"name": "FV Partner"})
        partner.company_ids = self.company_a + self.company_b
        as_merchant = partner.with_user(self.merchant_a)
        # Only the merchant's own company is exposed.
        self.assertEqual(as_merchant.own_company_ids, self.company_a)
        self.assertTrue(as_merchant.show_own_company_field)
        # Editing the own company keeps the hidden company B.
        as_merchant.own_company_ids = self.company_a
        self.assertIn(self.company_b, partner.company_ids)
