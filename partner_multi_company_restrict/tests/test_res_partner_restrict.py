# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPartnerRestrictCrossCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Restrict Co A"})
        cls.company_b = cls.env["res.company"].create({"name": "Restrict Co B"})
        cls.merchant_a = new_test_user(
            cls.env,
            login="restrict_merchant_a",
            groups="base.group_user,base.group_partner_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        # A regular colleague, SAME company as merchant_a: must stay
        # visible, this is normal Odoo behaviour and not touched.
        cls.colleague_a = new_test_user(
            cls.env,
            login="restrict_colleague_a",
            groups="base.group_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.partner_colleague_a = cls.colleague_a.partner_id
        # A regular internal user of company B: must be hidden (other
        # company).
        cls.internal_user_b = new_test_user(
            cls.env,
            login="restrict_internal_b",
            groups="base.group_user",
            company_id=cls.company_b.id,
            company_ids=[(6, 0, cls.company_b.ids)],
        )
        cls.partner_b = cls.internal_user_b.partner_id

    def test_same_company_colleague_is_visible(self):
        self.assertEqual(
            self.partner_colleague_a.with_user(self.merchant_a).name,
            self.partner_colleague_a.sudo().name,
        )

    def test_other_company_colleague_is_hidden(self):
        with self.assertRaises(AccessError):
            self.partner_b.with_user(self.merchant_a).name  # noqa: B018
        found = (
            self.env["res.partner"]
            .with_user(self.merchant_a)
            .search([("id", "=", self.partner_b.id)])
        )
        self.assertFalse(found)

    def test_own_contact_is_visible(self):
        partner_a = self.merchant_a.partner_id
        self.assertEqual(
            partner_a.with_user(self.merchant_a).name, partner_a.sudo().name
        )

    def test_shared_contact_is_visible(self):
        self.partner_b.sudo().company_ids = False
        self.assertEqual(
            self.partner_b.with_user(self.merchant_a).name,
            self.partner_b.sudo().name,
        )

    def test_multi_company_user_not_assigned_stays_scoped(self):
        # Deliberately no group-based bypass: a user with multi-company
        # access but only assigned to company A must NOT see company B's
        # colleague either.
        multi_company_user = new_test_user(
            self.env,
            login="restrict_multi_company_user",
            groups="base.group_user,base.group_multi_company",
            company_id=self.company_a.id,
            company_ids=[(6, 0, self.company_a.ids)],
        )
        with self.assertRaises(AccessError):
            self.partner_b.with_user(multi_company_user).name  # noqa: B018

    def test_user_assigned_to_both_companies_sees_both(self):
        # Once actually assigned to both companies (e.g. by
        # res_company_admin_sync, for a real administrator), a user sees
        # colleagues of either one -- no special-casing needed.
        both_companies_user = new_test_user(
            self.env,
            login="restrict_both_companies_user",
            groups="base.group_user,base.group_multi_company",
            company_id=self.company_a.id,
            company_ids=[(6, 0, (self.company_a + self.company_b).ids)],
        )
        self.assertEqual(
            self.partner_b.with_user(both_companies_user).name,
            self.partner_b.sudo().name,
        )

    def test_setting_toggle_disables_restriction(self):
        rule = self.env.ref(
            "partner_multi_company_restrict.res_partner_rule_restrict_cross_company"
        )
        rule.sudo().active = False
        try:
            found = (
                self.env["res.partner"]
                .with_user(self.merchant_a)
                .search([("id", "=", self.partner_b.id)])
            )
            self.assertTrue(found)
        finally:
            rule.sudo().active = True
