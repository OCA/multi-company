# Copyright 2017 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2018 Vicent Cubells - Tecnativa <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase, new_test_user, users


class TestsProductTaxMulticompany(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Company = cls.env["res.company"].with_context(tracking_disable=True)
        AccountTax = cls.env["account.tax"].with_context(tracking_disable=True)
        cls.IrDefault = cls.env["ir.default"].with_context(tracking_disable=True)
        cls.Product = cls.env["product.product"].with_context(tracking_disable=True)
        cls.company_1 = cls.Company.create({"name": "Test company 1"})
        cls.company_2 = cls.Company.create({"name": "Test company 2"})
        user_ctx = {
            "tracking_disable": True,
            "no_reset_password": True,
        }
        cls.user_1 = new_test_user(
            cls.env,
            login="user_1",
            groups="account.group_account_manager",
            context=user_ctx,
            company_id=cls.company_1.id,
            company_ids=[(6, 0, cls.company_1.ids)],
        )
        cls.user_2 = new_test_user(
            cls.env,
            login="user_2",
            groups="account.group_account_manager",
            context=user_ctx,
            company_id=cls.company_2.id,
            company_ids=[(6, 0, cls.company_2.ids)],
        )
        tax_vals = {
            "name": "Test Customer Tax 10%",
            "amount": 10.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        }
        cls.tax_10_cc1 = AccountTax.with_user(cls.user_1.id).create(tax_vals.copy())
        cls.tax_10_cc2 = AccountTax.with_user(cls.user_2.id).create(tax_vals.copy())
        tax_vals.update({"name": "Test Customer Tax 20%", "amount": 20.0})
        cls.tax_20_cc1 = AccountTax.with_user(cls.user_1.id).create(tax_vals.copy())
        cls.tax_20_cc2 = AccountTax.with_user(cls.user_2.id).create(tax_vals.copy())
        tax_vals.update(
            {
                "name": "Test Supplier Tax 10%",
                "amount": 10.0,
                "type_tax_use": "purchase",
            }
        )
        cls.tax_10_sc1 = AccountTax.with_user(cls.user_1.id).create(tax_vals.copy())
        cls.tax_10_sc2 = AccountTax.with_user(cls.user_2.id).create(tax_vals.copy())
        tax_vals.update({"name": "Test Supplier Tax 20%", "amount": 20.0})
        cls.tax_20_sc1 = AccountTax.with_user(cls.user_1.id).create(tax_vals.copy())
        cls.tax_20_sc2 = AccountTax.with_user(cls.user_2.id).create(tax_vals.copy())
        cls.company_1.write(
            {
                "account_sale_tax_id": cls.tax_10_cc1.id,
                "account_purchase_tax_id": cls.tax_10_sc1.id,
            }
        )
        cls.company_2.write(
            {
                "account_sale_tax_id": cls.tax_20_cc2.id,
                "account_purchase_tax_id": cls.tax_20_sc2.id,
            }
        )

    @users("user_1")
    def test_multicompany_default_tax(self):
        product = self.Product.with_user(self.env.user).create(
            {"name": "Test Product", "company_id": False}
        )
        product = product.sudo()
        self.assertIn(self.tax_10_cc1, product.taxes_id)
        self.assertIn(self.tax_20_cc2, product.taxes_id)
        self.assertIn(self.tax_10_sc1, product.supplier_taxes_id)
        self.assertIn(self.tax_20_sc2, product.supplier_taxes_id)

    @users("user_1")
    def test_not_default_tax_if_set(self):
        product = self.Product.with_user(self.env.user).create(
            {
                "name": "Test Product",
                "taxes_id": [(6, 0, self.tax_20_cc1.ids)],
                "supplier_taxes_id": [(6, 0, self.tax_20_sc1.ids)],
                "company_id": False,
            }
        )
        product = product.sudo()
        self.assertNotIn(self.tax_10_cc1, product.taxes_id)
        self.assertNotIn(self.tax_10_sc1, product.supplier_taxes_id)

    @users("user_2")
    def test_default_tax_if_set_match(self):
        product = self.Product.with_user(self.env.user).create(
            {
                "name": "Test Product",
                "taxes_id": [(6, 0, self.tax_20_cc2.ids)],
                "supplier_taxes_id": [(6, 0, self.tax_20_sc2.ids)],
                "company_id": False,
            }
        )
        product = product.sudo()
        self.assertIn(self.tax_10_cc1, product.taxes_id)
        self.assertIn(self.tax_10_sc1, product.supplier_taxes_id)

    @users("user_1")
    def test_tax_not_default_set_match(self):
        self.company_1.write({"account_sale_tax_id": self.tax_20_cc1.id})
        product = self.Product.with_user(self.env.user).create(
            {
                "name": "Test Product",
                "taxes_id": [(6, 0, self.tax_10_cc1.ids)],
                "supplier_taxes_id": [(6, 0, self.tax_10_sc1.ids)],
                "company_id": False,
            }
        )
        product = product.sudo()
        self.assertIn(self.tax_10_cc2, product.taxes_id)
        self.company_1.write({"account_sale_tax_id": self.tax_20_sc1.id})
        product = self.Product.with_user(self.env.user).create(
            {
                "name": "Test Product",
                "taxes_id": [(6, 0, self.tax_10_cc1.ids)],
                "supplier_taxes_id": [(6, 0, self.tax_10_sc1.ids)],
                "company_id": False,
            }
        )
        product = product.sudo()
        self.assertIn(self.tax_20_sc2, product.supplier_taxes_id)
