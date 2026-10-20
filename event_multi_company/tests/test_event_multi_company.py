# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestEventMultiCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.event_obj = cls.env["event.event"]
        cls.company_1 = cls.env["res.company"].create({"name": "Test company 1"})

    def _make_event_vals(self, name):
        today = fields.Datetime.now()
        return {
            "name": name,
            "date_begin": today + timedelta(days=10),
            "date_end": today + timedelta(days=11),
            "date_tz": "UTC",
        }

    def test_inherit_multi_company_abstract(self):
        # event.event has been mixed with multi.company.abstract: the M2M
        # company_ids field exists and company_id is now computed.
        self.assertIn("company_ids", self.event_obj._fields)
        self.assertTrue(self.event_obj._fields["company_id"].compute)

    def test_create_with_company_id_populates_company_ids(self):
        # The abstract's inverse copies company_id into company_ids on create.
        event = self.event_obj.create(
            {**self._make_event_vals("Test"), "company_id": self.company_1.id}
        )
        self.assertEqual(event.company_ids, self.company_1)

    def test_post_init_hook(self):
        # hooks.post_init_hook delegates to base_multi_company.fill_company_ids.
        # Running it on a freshly created event is a no-op (company_ids
        # already populated by the abstract's inverse) but exercises the
        # imports and the function call.
        from ..hooks import post_init_hook

        event = self.event_obj.create(
            {**self._make_event_vals("Hooked"), "company_id": self.company_1.id}
        )
        post_init_hook(self.env)
        event.invalidate_recordset(["company_ids"])
        self.assertIn(self.company_1, event.company_ids)
