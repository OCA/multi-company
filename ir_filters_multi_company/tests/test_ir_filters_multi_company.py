# Copyright 2026 Ahkio Oy
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from ..hooks.post_init_hook import post_init_hook


class TestIrFiltersMultiCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.ref("base.main_company")
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.user = cls.env["res.users"].create(
            {
                "name": "Filter User",
                "login": "filter_user",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, (cls.company_a | cls.company_b).ids)],
                "groups_id": [
                    (6, 0, [cls.env.ref("base.group_user").id]),
                ],
            }
        )

    def _filters(self, company):
        return (
            self.env["ir.filters"]
            .with_user(self.user)
            .with_context(allowed_company_ids=[company.id])
        )

    def _save(self, company, name, is_default=False, user=True):
        return self._filters(company).create_or_replace(
            {
                "name": name,
                "model_id": "res.partner",
                "domain": "[]",
                "context": "{}",
                "is_default": is_default,
                "user_id": self.user.id if user else False,
            }
        )

    def _names(self, company):
        return {
            f["name"]
            for f in self._filters(company).get_filters("res.partner")
            if f["name"] in ("A", "B", "Shared")
        }

    def test_saved_filter_gets_current_company(self):
        filter_a = self._save(self.company_a, "A")
        filter_b = self._save(self.company_b, "B")
        self.assertEqual(filter_a.company_id, self.company_a)
        self.assertEqual(filter_b.company_id, self.company_b)

    def test_filters_visible_only_in_their_company(self):
        self._save(self.company_a, "A")
        self._save(self.company_b, "B")
        self.env["ir.filters"].create(
            {"name": "Shared", "model_id": "res.partner", "company_id": False}
        )
        self.assertEqual(self._names(self.company_a), {"A", "Shared"})
        self.assertEqual(self._names(self.company_b), {"B", "Shared"})

    def test_default_filter_per_company(self):
        filter_a = self._save(self.company_a, "A", is_default=True)
        filter_b = self._save(self.company_b, "B", is_default=True)
        self.assertTrue(filter_a.is_default)
        self.assertTrue(filter_b.is_default)
        defaults_a = [
            f["name"]
            for f in self._filters(self.company_a).get_filters("res.partner")
            if f["is_default"]
        ]
        defaults_b = [
            f["name"]
            for f in self._filters(self.company_b).get_filters("res.partner")
            if f["is_default"]
        ]
        self.assertEqual(defaults_a, ["A"])
        self.assertEqual(defaults_b, ["B"])

    def test_new_default_replaces_default_of_same_company_only(self):
        filter_a = self._save(self.company_a, "A", is_default=True)
        filter_b = self._save(self.company_b, "B", is_default=True)
        self._save(self.company_a, "A2", is_default=True)
        self.assertFalse(filter_a.is_default)
        self.assertTrue(filter_b.is_default)

    def test_shared_default_per_company(self):
        self._save(self.company_a, "A", is_default=True, user=False)
        filter_b = self._save(self.company_b, "B", is_default=True, user=False)
        self.assertTrue(filter_b.is_default)

    def test_post_init_hook_assigns_creator_company(self):
        legacy = (
            self.env["ir.filters"]
            .with_user(self.user)
            .create({"name": "Legacy", "model_id": "res.partner", "company_id": False})
        )
        post_init_hook(self.env.cr, self.env.registry)
        legacy.invalidate_recordset()
        self.assertEqual(legacy.company_id, self.company_a)
