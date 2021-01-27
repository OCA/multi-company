# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


@common.at_install(False)
@common.post_install(True)
class TestPosCategoryMultiCompany(common.TransactionCase):
    def setUp(self):
        super().setUp()
        groups = self.env.ref("base.group_system")
        self.company_1 = self.env["res.company"].create({"name": "Test company 1"})
        self.company_2 = self.env["res.company"].create({"name": "Test company 2"})
        self.pos_category = self.env["pos.category"]
        self.pos_category_company_none = self.pos_category.create(
            {
                "name": "Product without company",
                "company_ids": [(6, 0, [])],
                "company_id": False,
            }
        )
        self.pos_category_company_1 = self.pos_category.create(
            {
                "name": "Pos category from company 1",
                "company_ids": [(6, 0, self.company_1.ids)],
            }
        )
        self.pos_category_company_2 = self.pos_category.create(
            {
                "name": "Pos category from company 2",
                "company_ids": [(6, 0, self.company_2.ids)],
            }
        )
        self.pos_category_company_both = self.pos_category.create(
            {
                "name": "Pos category for both companies",
                "company_ids": [(6, 0, (self.company_1 + self.company_2).ids)],
            }
        )
        self.user_company_1 = self.env["res.users"].create(
            {
                "name": "User company 1",
                "login": "user_company_1",
                "groups_id": [(6, 0, groups.ids)],
                "company_id": self.company_1.id,
                "company_ids": [(6, 0, self.company_1.ids)],
            }
        )
        self.user_company_2 = self.env["res.users"].create(
            {
                "name": "User company 2",
                "login": "user_company_2",
                "groups_id": [(6, 0, groups.ids)],
                "company_id": self.company_2.id,
                "company_ids": [(6, 0, self.company_2.ids)],
            }
        )

    def test_create_pos_category(self):
        pos_category = self.pos_category.create({"name": "Test"})
        company = self.env.company
        self.assertTrue(company.id in pos_category.company_ids.ids)

    def test_company_none(self):
        self.assertFalse(self.pos_category_company_none.company_id)

    def test_company_1(self):
        self.assertEqual(
            self.pos_category_company_1.with_user(self.user_company_1).company_id,
            self.company_1,
        )

    def test_company_2(self):
        self.assertEqual(
            self.pos_category_company_2.with_user(self.user_company_2).company_id,
            self.company_2,
        )
