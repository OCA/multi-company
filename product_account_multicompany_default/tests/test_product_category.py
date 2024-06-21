# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo.exceptions import UserError
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class ProductCategoryDefaultAccountsCase(AccountTestInvoicingCommon):
    @classmethod
    @mute_logger(
        "odoo.addons.product_account_multicompany_default.models.product_category"
    )
    def setUpClass(cls):
        super().setUpClass()
        # An income account with same code on both companies
        cls.account_income_a1 = cls.env["account.account"].create(
            {
                "name": "Income A1",
                "code": "INC.A",
                "account_type": "income",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.account_income_a2 = cls.env["account.account"].create(
            {
                "name": "Income A2",
                "code": "INC.A",
                "account_type": "income",
                "company_id": cls.company_data_2["company"].id,
            }
        )
        # An income account available only on company 1
        cls.account_income_b1 = cls.env["account.account"].create(
            {
                "name": "Income B1",
                "code": "INC.B",
                "account_type": "income",
                "company_id": cls.company_data["company"].id,
            }
        )
        # An expense account with same code on both companies
        cls.account_expense_a1 = cls.env["account.account"].create(
            {
                "name": "Expense A1",
                "code": "EXP.A",
                "account_type": "expense",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.account_expense_a2 = cls.env["account.account"].create(
            {
                "name": "Expense A2",
                "code": "EXP.A",
                "account_type": "expense",
                "company_id": cls.company_data_2["company"].id,
            }
        )
        # An expense account available only on company 1
        cls.account_expense_b1 = cls.env["account.account"].create(
            {
                "name": "Expense B1",
                "code": "EXP.B",
                "account_type": "expense",
                "company_id": cls.company_data["company"].id,
            }
        )

    def test_creation_product_category_propagation(self):
        """Accounts are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        product_cat = env["product.category"].create(
            {
                "name": "Test Category",
                "property_account_income_categ_id": self.account_income_a1.id,
                "property_account_expense_categ_id": self.account_expense_a1.id,
            }
        )
        product_cat_cp2 = product_cat.with_company(self.company_data_2["company"].id)
        self.assertEqual(
            product_cat_cp2.property_account_income_categ_id, self.account_income_a2
        )
        self.assertEqual(
            product_cat_cp2.property_account_expense_categ_id, self.account_expense_a2
        )

    def test_action_button_propagation(self):
        """Accounts are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A product created without accounts
        product_categ = env["product.category"].create(
            {
                "name": "Test Product Category",
            }
        )
        # Default categories are assigned on creation
        self.assertTrue(product_categ.property_account_income_categ_id)
        self.assertTrue(product_categ.property_account_expense_categ_id)
        product_categ_cp2 = product_categ.with_company(
            self.company_data_2["company"].id
        )
        # After writing accounts, they are still not propagated
        product_categ.write(
            {
                "property_account_income_categ_id": self.account_income_a1.id,
                "property_account_expense_categ_id": self.account_expense_a1.id,
            }
        )
        self.assertNotEqual(
            product_categ_cp2.property_account_income_categ_id, self.account_income_a2
        )
        # Propagating income account
        product_categ.propagate_multicompany_account_income()
        self.assertEqual(
            product_categ_cp2.property_account_income_categ_id, self.account_income_a2
        )
        # Propagating expense account
        product_categ.propagate_multicompany_account_expense()
        self.assertEqual(
            product_categ_cp2.property_account_expense_categ_id, self.account_expense_a2
        )

    def test_propagate_property_fields_without_accounts(self):
        """Accounts are not propagated when no account is selected"""
        env = self.env.user.with_company(self.company_data["company"].id).env
        self.env.user.company_ids = self.env["res.company"].browse(
            self.company_data["company"].id
        )
        product_categ = env["product.category"].create(
            {
                "name": "Test Product Category",
            }
        )
        self.assertFalse(product_categ._propagate_property_fields())

    def test_no_alien_companies(self):
        """Accounts are not propagated when user has access to only one company."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        self.env.user.company_ids = self.env["res.company"].browse(
            self.company_data["company"].id
        )
        product_categ = env["product.category"].create(
            {
                "name": "Test Product Category",
                "property_account_income_categ_id": self.account_income_a1.id,
            }
        )
        self.assertFalse(product_categ._propagate_property_fields())
        with self.assertRaises(UserError):
            product_categ.propagate_multicompany_account_income()

    def test_force_property_propagation(self):
        env = self.env.user.with_company(self.company_data["company"].id).env
        product_categ = env["product.category"].create(
            {
                "name": "Test Product Category",
                "property_account_income_categ_id": self.account_income_a1.id,
            }
        )

        product_categ = product_categ.with_context(force_property_propagation=True)
        product_categ.property_account_income_categ_id = self.account_income_a1

        product_categ_cp2 = product_categ.with_company(
            self.company_data_2["company"].id
        )
        self.assertEqual(
            product_categ_cp2.property_account_income_categ_id, self.account_income_a2
        )
