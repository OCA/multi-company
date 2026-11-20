# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestCrmLostReasonMultiCompany(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls._create_company(name="Company B")
        cls.reason_model = cls.env["crm.lost.reason"]
        cls.reason_a = cls.reason_model.create({"name": "Reason A"})
        cls.reason_b = cls.reason_model.create(
            {"name": "Reason B", "company_id": cls.company_b.id}
        )
        cls.reason_shared = cls.reason_model.create(
            {"name": "Reason Shared", "company_id": False}
        )
        cls.user_a = new_test_user(
            cls.env,
            login="crm_lost_reason_user_a",
            groups="sales_team.group_sale_salesman",
            company_id=cls.company_a.id,
            company_ids=[cls.company_a.id],
        )
        cls.lead_a = cls.env["crm.lead"].create(
            {"name": "Lead A", "company_id": cls.company_a.id}
        )
        cls.lead_b = cls.env["crm.lead"].create(
            {"name": "Lead B", "company_id": cls.company_b.id}
        )
        cls.lead_no_company = cls.env["crm.lead"].create(
            {"name": "Lead without company", "company_id": False}
        )

    def _mark_lost(self, leads, reason):
        return (
            self.env["crm.lead.lost"]
            .create({"lead_ids": leads.ids, "lost_reason_id": reason.id})
            .action_lost_reason_apply()
        )

    def test_default_company(self):
        self.assertEqual(self.reason_a.company_id, self.company_a)

    def test_record_rule(self):
        reasons = self.reason_a | self.reason_b | self.reason_shared
        visible = self.reason_model.with_user(self.user_a).search(
            [("id", "in", reasons.ids)]
        )
        self.assertEqual(visible, self.reason_a | self.reason_shared)

    def test_lead_lost_reason_company(self):
        for leads, reason in [
            (self.lead_a, self.reason_a),
            (self.lead_a | self.lead_b | self.lead_no_company, self.reason_shared),
        ]:
            with self.subTest(leads=leads.mapped("name"), reason=reason.name):
                self._mark_lost(leads, reason)
                self.assertEqual(leads.lost_reason_id, reason)
                leads.action_unarchive()

    def test_lead_lost_reason_other_company(self):
        for leads, reason in [
            (self.lead_a, self.reason_b),
            (self.lead_no_company, self.reason_a),
            (self.lead_a | self.lead_b, self.reason_a),
        ]:
            with (
                self.subTest(leads=leads.mapped("name"), reason=reason.name),
                self.assertRaises(UserError),
            ):
                self._mark_lost(leads, reason)
