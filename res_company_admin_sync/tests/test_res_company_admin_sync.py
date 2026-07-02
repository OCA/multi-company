# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestResCompanyAdminSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = new_test_user(
            cls.env,
            login="sync_admin",
            groups="base.group_system,base.group_multi_company",
        )
        cls.merchant = new_test_user(
            cls.env, login="sync_merchant", groups="base.group_user"
        )

    def test_new_company_added_to_admin(self):
        before = set(self.admin.company_ids.ids)
        company = self.env["res.company"].create({"name": "Sync Test Co"})
        self.assertIn(company.id, self.admin.company_ids.ids)
        self.assertNotIn(company.id, before)

    def test_new_company_not_added_to_regular_user(self):
        company = self.env["res.company"].create({"name": "Sync Test Co 2"})
        self.assertNotIn(company.id, self.merchant.company_ids.ids)

    def test_multiple_companies_created_together(self):
        before = set(self.admin.company_ids.ids)
        companies = self.env["res.company"].create(
            [{"name": "Sync Multi A"}, {"name": "Sync Multi B"}]
        )
        after = set(self.admin.company_ids.ids)
        self.assertTrue(set(companies.ids).issubset(after))
        self.assertTrue(set(companies.ids).isdisjoint(before))

    def test_promoting_user_to_admin_grants_all_companies(self):
        company = self.env["res.company"].create({"name": "Sync Promote Co"})
        self.assertNotIn(company.id, self.merchant.company_ids.ids)
        self.merchant.write({"group_ids": [(4, self.env.ref("base.group_system").id)]})
        self.assertIn(company.id, self.merchant.company_ids.ids)
