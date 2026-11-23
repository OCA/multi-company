# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestCrmTagMultiCompany(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.tag_a = cls.env["crm.tag"].create(
            {"name": "Tag A", "company_id": cls.company_a.id}
        )
        cls.tag_b = cls.env["crm.tag"].create(
            {"name": "Tag B", "company_id": cls.company_b.id}
        )
        cls.tag_shared = cls.env["crm.tag"].create(
            {"name": "Tag Shared", "company_id": False}
        )
        cls.salesman = new_test_user(
            cls.env,
            login="crm_tag_salesman",
            groups="sales_team.group_sale_salesman",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )

    def test_default_company(self):
        tag = self.env["crm.tag"].with_company(self.company_b).create({"name": "New"})
        self.assertEqual(tag.company_id, self.company_b)

    def test_record_rule(self):
        tags = (
            self.env["crm.tag"]
            .with_user(self.salesman)
            .search([("id", "in", (self.tag_a | self.tag_b | self.tag_shared).ids)])
        )
        self.assertEqual(tags, self.tag_a | self.tag_shared)

    def test_lead_tag_company_check(self):
        for tags in (self.tag_a, self.tag_shared, self.tag_a | self.tag_shared):
            with self.subTest(tags=tags.mapped("name")):
                lead = self.env["crm.lead"].create(
                    {
                        "name": "Lead",
                        "company_id": self.company_a.id,
                        "tag_ids": [Command.set(tags.ids)],
                    }
                )
                self.assertEqual(lead.tag_ids, tags)
        leads = self.env["crm.lead"].create(
            [
                {"name": "Lead A", "company_id": self.company_a.id},
                {"name": "Lead B", "company_id": self.company_b.id},
            ]
        )
        leads.tag_ids = [Command.link(self.tag_shared.id)]
        self.assertEqual(leads.tag_ids, self.tag_shared)
        with self.assertRaises(UserError):
            leads[0].tag_ids = [Command.link(self.tag_b.id)]
        with self.assertRaises(UserError):
            self.env["crm.lead"].create(
                [
                    {"name": "Lead OK", "company_id": self.company_b.id},
                    {
                        "name": "Lead KO",
                        "company_id": self.company_a.id,
                        "tag_ids": [Command.link(self.tag_b.id)],
                    },
                ]
            )
