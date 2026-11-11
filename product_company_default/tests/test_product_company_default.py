# Copyright 2026 Canarias Conectada
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductCompanyDefault(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, test_product_company_default=True)
        )
        cls.company_a = cls.env["res.company"].create({"name": "PCD Test Co A"})
        cls.company_b = cls.env["res.company"].create({"name": "PCD Test Co B"})
        cls.merchant = new_test_user(
            cls.env,
            login="pcd_test_merchant",
            groups="base.group_user,product.group_product_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.multi_company_manager = new_test_user(
            cls.env,
            login="pcd_test_multi_company_manager",
            groups=(
                "base.group_user,product.group_product_manager,base.group_multi_company"
            ),
            company_id=cls.company_a.id,
            company_ids=[(6, 0, (cls.company_a + cls.company_b).ids)],
        )
        cls.Product = cls.env["product.template"]

    def test_no_company_info_gets_the_active_company(self):
        product = self.Product.with_user(self.merchant).create({"name": "PCD P1"})
        self.assertEqual(product.sudo().company_ids, self.company_a)

    def test_explicit_companies_are_respected(self):
        product = self.Product.with_user(self.multi_company_manager).create(
            {
                "name": "PCD P2",
                "company_ids": [Command.set((self.company_a + self.company_b).ids)],
            }
        )
        self.assertEqual(product.sudo().company_ids, self.company_a + self.company_b)

    def test_explicit_empty_by_regular_user_is_scoped(self):
        # A non multi-company user (the field is hidden from them; only
        # reachable through RPC/imports) must not be able to create a
        # global product by sending an emptying command: plain truthiness
        # would have treated [Command.set([])] as an explicit choice.
        product = self.Product.with_user(self.merchant).create(
            {"name": "PCD P3", "company_ids": [Command.set([])]}
        )
        self.assertEqual(product.sudo().company_ids, self.company_a)

    def test_explicit_empty_by_multi_company_user_stays_global(self):
        product = self.Product.with_user(self.multi_company_manager).create(
            {"name": "PCD P4", "company_ids": [Command.set([])]}
        )
        self.assertFalse(product.sudo().company_ids)
