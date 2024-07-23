# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductCategoryMulti(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.main_company = cls.env.ref("base.main_company")
        cls.company_A = cls.env["res.company"].create(
            {
                "name": "company A",
                "parent_id": cls.main_company.id,
            }
        )
        cls.company_B = cls.env["res.company"].create(
            {
                "name": "Company B",
                "parent_id": cls.main_company.id,
            }
        )
        cls.company_C = cls.env["res.company"].create(
            {
                "name": "company C",
                "parent_id": cls.main_company.id,
            }
        )
        cls.company_D = cls.env["res.company"].create(
            {
                "name": "Company D",
                "parent_id": cls.main_company.id,
            }
        )
        cls.all_company_ids = [
            cls.main_company.id,
            cls.company_A.id,
            cls.company_B.id,
            cls.company_C.id,
            cls.company_D.id,
        ]

        cls.category = cls.env["product.category"]
        cls.product = cls.env["product.template"]

        cls.categ_ALL = cls.category.create(
            {
                "name": "Category ALL",
                "company_ids": [(6, 0, cls.all_company_ids)],
            }
        )
        cls.categ_A = cls.category.create(
            {
                "name": "Category A",
                "company_ids": [(6, 0, [cls.company_A.id])],
                "parent_id": cls.categ_ALL.id,
            }
        )
        cls.categ_AB = cls.category.create(
            {
                "name": "Category AB",
                "company_ids": [(6, 0, [cls.company_A.id, cls.company_B.id])],
                "parent_id": cls.categ_ALL.id,
            }
        )
        cls.product_A = cls.product.create(
            {
                "name": "Product A",
                "company_ids": [(6, 0, [cls.company_A.id])],
                "categ_id": cls.categ_AB.id,
            }
        )
        cls.product_B = cls.product.create(
            {
                "name": "Product B",
                "company_ids": [(6, 0, [cls.company_A.id])],
                "categ_id": cls.categ_AB.id,
            }
        )
        cls.product_C = cls.product.create(
            {
                "name": "Product C",
                "company_ids": [(6, 0, [cls.company_C.id])],
                "categ_id": cls.categ_ALL.id,
            }
        )

    def test_category_company_restriction(self):
        # Check that new categories are created correctly
        new_categories = [self.categ_A.id, self.categ_AB.id, self.categ_ALL.id]
        categ_list = self.env["product.category"].search([("id", "in", new_categories)])
        self.assertEqual(len(categ_list), 3)

        # Check that new products are created correctly
        product_list = self.env["product.template"].search(
            [("categ_id", "in", new_categories)]
        )
        self.assertEqual(len(product_list), 3)

        # Check Category Constrains
        with self.assertRaises(ValidationError):
            self.categ_C = self.category.create(
                {
                    "name": "Category C",
                    "company_ids": [(6, 0, [self.company_C.id])],
                    "parent_id": self.categ_A.id,
                }
            )

        with self.assertRaises(ValidationError):
            self.categ_AB.company_ids = [(6, 0, [self.company_B.id])]

        # Check Product Constrains
        with self.assertRaises(ValidationError):
            self.product_D = self.product.create(
                {
                    "name": "Product D",
                    "company_ids": [(6, 0, [self.company_D.id])],
                    "categ_id": self.categ_AB.id,
                }
            )
