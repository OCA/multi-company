# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductOwnCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Opt this run into the "never blank" constraint (skipped by default
        # during tests so other modules keep their global-by-default checks).
        cls.env = cls.env(
            context=dict(cls.env.context, test_multi_company_field_visible=True)
        )
        cls.company_a = cls.env["res.company"].create({"name": "Field Visible A"})
        cls.company_b = cls.env["res.company"].create({"name": "Field Visible B"})
        # Merchant: a plain internal user owning a single company (so it does
        # NOT get base.group_multi_company).
        # A realistic merchant: can manage products, owns a single company
        # (so no base.group_multi_company) and cannot read other companies.
        cls.merchant_a = new_test_user(
            cls.env,
            login="fv_merchant_a",
            groups="base.group_user,product.group_product_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.Product = cls.env["product.template"]

    def _product(self, company_ids):
        return self.Product.create(
            {"name": "FV Product", "company_ids": [(6, 0, company_ids)]}
        )

    def test_compute_shows_only_own_company(self):
        product = self._product((self.company_a + self.company_b).ids)
        as_merchant = product.with_user(self.merchant_a)
        self.assertEqual(as_merchant.own_company_ids, self.company_a)
        self.assertTrue(as_merchant.show_own_company_field)

    def test_inverse_preserves_hidden_companies(self):
        product = self._product((self.company_a + self.company_b).ids)
        product.with_user(self.merchant_a).own_company_ids = self.company_a
        # Company B (invisible to the merchant) must survive the edit.
        self.assertIn(self.company_b, product.company_ids)
        self.assertIn(self.company_a, product.company_ids)

    def test_never_blank_falls_back_to_own_company(self):
        product = self._product(self.company_a.ids)
        product.with_user(self.merchant_a).own_company_ids = False
        self.assertEqual(product.company_ids, self.company_a)

    def test_cannot_escalate_to_foreign_company(self):
        product = self._product(self.company_a.ids)
        # The merchant cannot even read company B, so assigning it fails closed.
        with self.assertRaises(AccessError):
            product.with_user(self.merchant_a).own_company_ids = self.company_b

    def test_multi_company_user_field_hidden(self):
        product = self._product(self.company_a.ids)
        admin = self.env.ref("base.user_admin")
        admin.write({"company_ids": [(4, self.company_b.id)]})
        self.assertTrue(admin.has_group("base.group_multi_company"))
        self.assertFalse(product.with_user(admin).show_own_company_field)

    def test_settings_toggle_hides_field(self):
        product = self._product(self.company_a.ids)
        param = self.env["ir.config_parameter"].sudo()
        param.set_param("multi_company_field_visible.product", "False")
        product.invalidate_recordset()
        self.assertFalse(product.with_user(self.merchant_a).show_own_company_field)
        param.set_param("multi_company_field_visible.product", "True")
        product.invalidate_recordset()
        self.assertTrue(product.with_user(self.merchant_a).show_own_company_field)
