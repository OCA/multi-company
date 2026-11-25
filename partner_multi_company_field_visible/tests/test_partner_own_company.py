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

    def test_multi_company_user_partial_active_selection_does_not_crash(self):
        # A multi-company user (own_company_ids hidden for them) belonging
        # to two companies but with only ONE of them active in the company
        # switcher (allowed_company_ids) must not crash reading a partner
        # shared between both -- own_company_ids' compute must not attempt
        # to touch the company that is not part of the active selection.
        multi_company_user = new_test_user(
            self.env,
            login="fv_partner_multi_company_user",
            groups="base.group_user,base.group_multi_company",
            company_id=self.company_a.id,
            company_ids=[(6, 0, (self.company_a + self.company_b).ids)],
        )
        partner = self.Partner.create({"name": "FV Partner Shared"})
        partner.company_ids = self.company_a + self.company_b
        narrowed = partner.with_user(multi_company_user).with_context(
            allowed_company_ids=self.company_a.ids
        )
        narrowed.invalidate_recordset()
        self.assertFalse(narrowed.show_own_company_field)
        self.assertEqual(
            narrowed.read(["own_company_ids"]),
            [{"id": partner.id, "own_company_ids": []}],
        )
