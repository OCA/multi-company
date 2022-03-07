# Copyright 2017 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2018 Vicent Cubells - Tecnativa <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestsProductTaxMulticompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestsProductTaxMulticompany, cls).setUpClass()
        default_country = cls.env.ref("base.cl")
        cls.company_1 = cls.env["res.company"].create(
            {"name": "Test company 1", "country_id": default_country.id}
        )
        cls.company_2 = cls.env["res.company"].create(
            {"name": "Test company 2", "country_id": default_country.id}
        )
        group_account_manager = cls.env.ref("account.group_account_manager")
        ResUsers = cls.env["res.users"]
        cls.user_1 = ResUsers.create(
            {
                "name": "User not admin",
                "login": "user_1",
                "email": "test@test.com",
                "groups_id": [(6, 0, group_account_manager.ids)],
                "company_id": cls.company_1.id,
                "company_ids": [(6, 0, cls.company_1.ids)],
            }
        )
        cls.user_2 = ResUsers.create(
            {
                "name": "User not admin",
                "login": "user_2",
                "email": "test@test.com",
                "groups_id": [(6, 0, group_account_manager.ids)],
                "company_id": cls.company_2.id,
                "company_ids": [(6, 0, cls.company_2.ids)],
            }
        )
        AccountTax = cls.env["account.tax"]
        tax_vals = {
            "name": "Test Customer Tax 10%",
            "amount": 10.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        }
        cls.tax_10_cc1 = AccountTax.with_user(cls.user_1.id).create(tax_vals)
        cls.tax_10_cc2 = AccountTax.with_user(cls.user_2.id).create(tax_vals)
        tax_vals.update({"name": "Test Customer Tax 20%", "amount": 20.0})
        cls.tax_20_cc1 = AccountTax.with_user(cls.user_1.id).create(tax_vals)
        cls.tax_20_cc2 = AccountTax.with_user(cls.user_2.id).create(tax_vals)
        tax_vals.update(
            {
                "name": "Test Supplier Tax 10%",
                "amount": 10.0,
                "type_tax_use": "purchase",
            }
        )
        cls.tax_10_sc1 = AccountTax.with_user(cls.user_1.id).create(tax_vals)
        cls.tax_10_sc2 = AccountTax.with_user(cls.user_2.id).create(tax_vals)
        tax_vals.update({"name": "Test Supplier Tax 20%", "amount": 20.0})
        cls.tax_20_sc1 = AccountTax.with_user(cls.user_1.id).create(tax_vals)
        cls.tax_20_sc2 = AccountTax.with_user(cls.user_2.id).create(tax_vals)
        cls.company_1.account_sale_tax_id = cls.tax_10_cc1.id
        cls.company_1.account_purchase_tax_id = cls.tax_10_sc1.id
        cls.company_2.account_sale_tax_id = cls.tax_20_cc2.id
        cls.company_2.account_purchase_tax_id = cls.tax_20_sc2.id

    def test_multicompany_default_tax(self):
        product = (
            self.env["product.product"]
            .with_user(self.user_1.id)
            .create({"name": "Test Product", "company_id": False})
        )
        product = product.sudo()
        self.assertIn(self.tax_10_cc1, product.taxes_id)
        self.assertIn(self.tax_20_cc2, product.taxes_id)
        self.assertIn(self.tax_10_sc1, product.supplier_taxes_id)
        self.assertIn(self.tax_20_sc2, product.supplier_taxes_id)

    def test_not_default_tax_if_set(self):
        product = (
            self.env["product.product"]
            .with_user(self.user_1.id)
            .create(
                {
                    "name": "Test Product",
                    "taxes_id": [(6, 0, self.tax_20_cc1.ids)],
                    "supplier_taxes_id": [(6, 0, self.tax_20_sc1.ids)],
                    "company_id": False,
                }
            )
        )
        product = product.sudo()
        self.assertNotIn(self.tax_10_cc1, product.taxes_id)
        self.assertNotIn(self.tax_10_sc1, product.supplier_taxes_id)

    def test_default_tax_if_set_match(self):
        product = (
            self.env["product.product"]
            .with_user(self.user_2.id)
            .create(
                {
                    "name": "Test Product",
                    "taxes_id": [(6, 0, self.tax_20_cc2.ids)],
                    "supplier_taxes_id": [(6, 0, self.tax_20_sc2.ids)],
                    "company_id": False,
                }
            )
        )
        product = product.sudo()
        self.assertIn(self.tax_10_cc1, product.taxes_id)
        self.assertIn(self.tax_10_sc1, product.supplier_taxes_id)

    def test_tax_not_default_set_match(self):
        self.company_1.account_sale_tax_id = self.tax_20_cc1.id
        self.company_1.account_purchase_tax_id = self.tax_20_sc1.id
        product = (
            self.env["product.product"]
            .with_user(self.user_1.id)
            .create(
                {
                    "name": "Test Product",
                    "taxes_id": [(6, 0, self.tax_10_cc1.ids)],
                    "supplier_taxes_id": [(6, 0, self.tax_10_sc1.ids)],
                    "company_id": False,
                }
            )
        )
        product = product.sudo()
        self.assertIn(self.tax_10_cc2, product.taxes_id)
        self.assertIn(self.tax_10_sc2, product.supplier_taxes_id)
