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

    def test_categ_different_company_id(self):
        self.categ_2.parent_id = self.categ_1
        with self.assertRaises(UserError):
            self.categ_2.company_id = self.company2
        with self.assertRaises(UserError):
            self.categ_2.company_id = False
        with self.assertRaises(UserError):
            self.categ_1.company_id = self.company2
        with self.assertRaises(UserError):
            self.categ_1.company_id = False

    def test_product_different_categ_id(self):
        product = self.env["product.template"].create(
            {
                "name": "Test product",
                "categ_id": self.categ_1.id,
                "company_id": self.company1.id,
            }
        )
        # No error.
        product.categ_id = self.categ_2
        # A really weird case... Maybe this shouldn't be possible.
        product.categ_id = self.categ_3

    def test_two_users_different_companies_same_product(self):
        """A user that is not a member of `base.group_multi_company`
        (mono-company user) creates a product, then a different user belonging
        to a different company wants to read it.
        """
        # Products have company_id=False by default
        product = (
            self.env["product.template"]
            .with_user(self.user1)
            .create(
                {
                    "name": "Test Product",
                    "categ_id": self.categ_1.id,
                }
            )
        )
        # User 2 can read the category. The user must be able to read it,
        # otherwise the product breaks for the user.
        self.assertEqual(product.with_user(self.user2).categ_id.name, self.categ_1.name)
