# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductCategoryMultiCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company1 = cls.env.ref("base.main_company")
        cls.company2 = cls.env["res.company"].create(
            {
                "name": "company 2",
                "parent_id": cls.env.ref("base.main_company").id,
            }
        )
        cls.user1 = cls.env.ref("base.user_admin")
        cls.user2 = cls.user1.copy(
            {
                "company_id": cls.company2.id,
                "company_ids": [(6, 0, [cls.company2.id])],
            }
        )

        cls.category = cls.env["product.category"]

        cls.categ_1 = cls.category.create(
            {
                "name": "one",
                "company_id": cls.company1.id,
            }
        )
        cls.categ_2 = cls.category.create(
            {
                "name": "two",
                "company_id": cls.company1.id,
            }
        )
        cls.categ_3 = cls.category.create(
            {
                "name": "three",
                "company_id": cls.company2.id,
            }
        )
        cls.categ_4 = cls.category.create(
            {
                "name": "four",
                "parent_id": cls.categ_1.id,
                "company_id": cls.company1.id,
            }
        )

    def test_1(self):
        new_categories = [self.categ_1.id, self.categ_2.id, self.categ_3.id]
        categ_list_1 = (
            self.env["product.category"]
            .with_user(self.user1.id)
            .search([("id", "in", new_categories)])
        )
        self.assertEqual(len(categ_list_1), 2)

        categ_list_2 = (
            self.env["product.category"]
            .with_user(self.user2.id)
            .search([("id", "in", new_categories)])
        )
        self.assertEqual(len(categ_list_2), 1)

        # Child category must belong to the same company as the parent category
        with self.assertRaises(UserError):
            self.categ_4.write({"company_id": self.company2.id})
