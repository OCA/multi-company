# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestPartnerCategoryMultiCompany(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.Category = cls.env["res.partner.category"]
        cls.tag_a = cls.Category.create(
            {"name": "Tag A", "company_id": cls.company_a.id}
        )
        cls.tag_b = cls.Category.create(
            {"name": "Tag B", "company_id": cls.company_b.id}
        )
        cls.tag_shared = cls.Category.create({"name": "Tag Shared"})
        cls.user = new_test_user(
            cls.env,
            login="partner_tag_user",
            groups="base.group_user,base.group_partner_manager",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )

    def test_record_rule(self):
        tags = self.Category.with_user(self.user).search(
            [("id", "in", (self.tag_a | self.tag_b | self.tag_shared).ids)]
        )
        self.assertEqual(tags, self.tag_a | self.tag_shared)

    def test_partner_tag_company_check(self):
        for tags in (self.tag_a, self.tag_shared, self.tag_a | self.tag_shared):
            with self.subTest(tags=tags.mapped("name")):
                partner = self.env["res.partner"].create(
                    {
                        "name": "Partner",
                        "company_id": self.company_a.id,
                        "category_id": [Command.set(tags.ids)],
                    }
                )
                self.assertEqual(partner.category_id, tags)
        partners = self.env["res.partner"].create(
            [
                {"name": "Partner A", "company_id": self.company_a.id},
                {"name": "Partner B", "company_id": self.company_b.id},
            ]
        )
        partners.category_id = [Command.link(self.tag_shared.id)]
        self.assertEqual(partners.category_id, self.tag_shared)
        with self.assertRaises(UserError):
            partners[0].category_id = [Command.link(self.tag_b.id)]
        with self.assertRaises(UserError):
            self.env["res.partner"].create(
                [
                    {"name": "Partner OK", "company_id": self.company_b.id},
                    {
                        "name": "Partner KO",
                        "company_id": self.company_a.id,
                        "category_id": [Command.link(self.tag_b.id)],
                    },
                ]
            )

    def test_partner_company_change(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Partner",
                "company_id": self.company_a.id,
                "category_id": [Command.link(self.tag_a.id)],
            }
        )
        with self.assertRaises(UserError):
            partner.company_id = self.company_b

    def test_parent_tag_company_check(self):
        child = self.Category.create(
            {
                "name": "Child",
                "company_id": self.company_a.id,
                "parent_id": self.tag_shared.id,
            }
        )
        self.assertEqual(child.display_name, "Tag Shared / Child")
        with self.assertRaises(UserError):
            child.parent_id = self.tag_b
        arch = self.Category.get_view(
            self.env.ref("base.view_partner_category_list").id, "list"
        )["arch"]
        parent_field = etree.fromstring(arch).xpath("//field[@name='parent_id']")[0]
        self.assertIn("company_id", parent_field.get("domain"))
