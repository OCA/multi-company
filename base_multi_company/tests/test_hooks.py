# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo.tests import common

from ..hooks import post_init_hook, uninstall_hook


class TestHooks(common.TransactionCase):
    def test_post_init_and_uninstall_hooks(self):
        """Ensure hooks apply."""

        access = self.env["ir.access"].create(
            {
                "name": "Test Multi Company Access",
                "model_id": self.env["ir.model"]
                .search([("model", "=", "res.users")])
                .id,
                "group_id": self.ref("base.group_user"),
                "operation": "crud",
                "domain": "[(1, '=', 1)]",
            }
        )

        self.env["ir.model.data"].create(
            {
                "name": "test_dummy_rule",
                "module": "base_multi_company_test",
                "model": "ir.access",
                "res_id": access.id,
            }
        )
        rule_ref = "base_multi_company_test.test_dummy_rule"

        with self.assertWarns(DeprecationWarning):
            post_init_hook(self.env, rule_ref, "res.users")

        self.assertTrue(access.active)
        self.assertIn("company_ids", access.domain)

        with self.assertWarns(DeprecationWarning):
            uninstall_hook(self.env, rule_ref)

        self.assertFalse(access.active)
        self.assertIn("company_ids", access.domain)
