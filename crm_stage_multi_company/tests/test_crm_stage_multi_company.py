# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestCrmStageMultiCompany(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls._create_company(name="Company B")
        cls.stage_model = cls.env["crm.stage"]
        cls.stage_a = cls.stage_model.create({"name": "Stage A", "sequence": 0})
        cls.stage_b = cls.stage_model.create(
            {"name": "Stage B", "sequence": 0, "company_id": cls.company_b.id}
        )
        cls.stage_b_won = cls.stage_model.create(
            {
                "name": "Stage B Won",
                "sequence": 90,
                "is_won": True,
                "company_id": cls.company_b.id,
            }
        )
        cls.stage_shared = cls.stage_model.create(
            {"name": "Stage Shared", "sequence": 0, "company_id": False}
        )
        cls.user_a = new_test_user(
            cls.env,
            login="crm_stage_user_a",
            groups="sales_team.group_sale_manager",
            company_id=cls.company_a.id,
            company_ids=[cls.company_a.id],
        )
        cls.user_ab = new_test_user(
            cls.env,
            login="crm_stage_user_ab",
            groups="sales_team.group_sale_salesman_all_leads",
            company_id=cls.company_a.id,
            company_ids=[cls.company_a.id, cls.company_b.id],
        )
        cls.lead_model_ab = (
            cls.env["crm.lead"]
            .with_user(cls.user_ab)
            .with_context(allowed_company_ids=[cls.company_a.id, cls.company_b.id])
        )

    def test_default_company(self):
        self.assertEqual(self.stage_a.company_id, self.company_a)

    def test_record_rule(self):
        stage_model = self.stage_model.with_user(self.user_a)
        visible = stage_model.search([("company_id", "!=", self.company_a.id)])
        self.assertEqual(visible, self.stage_shared)
        for operation in ("create", "write", "unlink"):
            with self.subTest(operation=operation), self.assertRaises(AccessError):
                if operation == "create":
                    stage_model.create(
                        {"name": "Stage", "company_id": self.company_b.id}
                    )
                elif operation == "write":
                    self.stage_b.with_user(self.user_a).write({"name": "Stage"})
                else:
                    self.stage_b.with_user(self.user_a).unlink()

    def test_read_group_stage_ids(self):
        groups = (
            self.env["crm.lead"]
            .with_user(self.user_a)
            .with_context(read_group_expand=True)
            .web_read_group([], ["stage_id"], ["__count"])["groups"]
        )
        stage_ids = {group["stage_id"][0] for group in groups}
        self.assertIn(self.stage_a.id, stage_ids)
        self.assertIn(self.stage_shared.id, stage_ids)
        self.assertNotIn(self.stage_b.id, stage_ids)

    def test_lead_stage_company(self):
        leads = self.lead_model_ab.create(
            [
                {"name": "Lead A", "company_id": self.company_a.id},
                {"name": "Lead B", "company_id": self.company_b.id},
                {"name": "Lead no company", "user_id": False, "team_id": False},
            ]
        )
        self.assertFalse(leads[2].company_id)
        self.assertEqual(
            [lead.stage_id for lead in leads],
            [self.stage_a, self.stage_b, self.stage_shared],
        )

    def test_lead_company_change(self):
        lead = self.lead_model_ab.create(
            {"name": "Lead", "company_id": self.company_a.id}
        )
        self.assertEqual(lead.stage_id, self.stage_a)
        lead.company_id = self.company_b
        self.assertEqual(lead.stage_id, self.stage_b)
        lead.write({"company_id": self.company_a.id, "stage_id": self.stage_shared.id})
        self.assertEqual(lead.stage_id, self.stage_shared)

    def test_lead_set_won(self):
        leads = self.lead_model_ab.create(
            [
                {"name": "Lead A", "company_id": self.company_a.id},
                {"name": "Lead B", "company_id": self.company_b.id},
            ]
        )
        leads.action_set_won()
        self.assertTrue(all(leads.stage_id.mapped("is_won")))
        self.assertEqual(leads[1].stage_id, self.stage_b_won)
        self.assertEqual(leads[0].stage_id.company_id, self.company_a)

    def test_lead_form_stage_domain(self):
        arch = self.env["crm.lead"].get_view(
            self.env.ref("crm.crm_lead_view_form").id, "form"
        )["arch"]
        stage = etree.fromstring(arch).xpath("//header/field[@name='stage_id']")[0]
        self.assertIn("('company_id', 'in', [company_id, False])", stage.get("domain"))
