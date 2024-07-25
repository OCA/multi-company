# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.product.tests.common import TestProductCommon


@tagged("post_install", "-at_install")
class ProductDefaultAccountsCase(AccountTestInvoicingCommon, TestProductCommon):
    @classmethod
    @mute_logger("odoo.addons.product_account_multicompany_default.models.product")
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

    def test_creation_propagation(self):
        """Accounts are propagated on creation."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        product_tmpl = env["product.template"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "property_account_income_id": self.account_income_a1.id,
                "property_account_expense_id": self.account_expense_a1.id,
            }
        )
        product_tmpl_cp2 = product_tmpl.with_company(self.company_data_2["company"].id)
        self.assertEqual(
            product_tmpl_cp2.property_account_income_id, self.account_income_a2
        )
        self.assertEqual(
            product_tmpl_cp2.property_account_expense_id, self.account_expense_a2
        )

    @mute_logger("odoo.addons.product_account_multicompany_default.models.product")
    def test_creation_no_propagation(self):
        """Accounts are not propagated on creation if they don't exist."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        product_tmpl = env["product.template"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "property_account_income_id": self.account_income_b1.id,
                "property_account_expense_id": self.account_expense_b1.id,
            }
        )
        product_tmpl_cp2 = product_tmpl.with_company(self.company_data_2["company"].id)
        self.assertFalse(product_tmpl_cp2.property_account_income_id)
        self.assertFalse(product_tmpl_cp2.property_account_expense_id)

    def test_action_button_propagation(self):
        """Accounts are propagated when user chooses to."""
        env = self.env.user.with_company(self.company_data["company"].id).env
        # A product created without accounts
        product_tmpl = env["product.template"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )
        self.assertFalse(product_tmpl.property_account_income_id)
        self.assertFalse(product_tmpl.property_account_expense_id)
        product_tmpl_cp2 = product_tmpl.with_company(self.company_data_2["company"].id)
        self.assertFalse(product_tmpl_cp2.property_account_income_id)
        self.assertFalse(product_tmpl_cp2.property_account_expense_id)
        # After writing accounts, they are still not propagated
        product_tmpl.write(
            {
                "property_account_income_id": self.account_income_a1.id,
                "property_account_expense_id": self.account_expense_a1.id,
            }
        )
        self.assertFalse(product_tmpl_cp2.property_account_income_id)
        self.assertFalse(product_tmpl_cp2.property_account_expense_id)
        # Propagating income account
        product_tmpl.propagate_multicompany_account_income()
        self.assertEqual(
            product_tmpl_cp2.property_account_income_id, self.account_income_a2
        )
        self.assertFalse(product_tmpl_cp2.property_account_expense_id)
        # Propagating expense account
        product_tmpl.propagate_multicompany_account_expense()
        self.assertEqual(
            product_tmpl_cp2.property_account_income_id, self.account_income_a2
        )
        self.assertEqual(
            product_tmpl_cp2.property_account_expense_id, self.account_expense_a2
        )
