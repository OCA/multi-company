# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.base.tests.common import BaseCommon


class TestCrmTagMultiCompanySale(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})
        cls.tag_a = cls.env["crm.tag"].create(
            {"name": "Tag A", "company_id": cls.company_a.id}
        )
        cls.tag_b = cls.env["crm.tag"].create(
            {"name": "Tag B", "company_id": cls.company_b.id}
        )
        cls.tag_shared = cls.env["crm.tag"].create(
            {"name": "Tag Shared", "company_id": False}
        )

    def _order_vals(self, company, tags=None):
        return {
            "partner_id": self.partner.id,
            "company_id": company.id,
            "tag_ids": [Command.set(tags.ids if tags else [])],
        }

    def test_order_tag_company_check(self):
        for tags in (self.tag_a, self.tag_shared, self.tag_a | self.tag_shared):
            with self.subTest(tags=tags.mapped("name")):
                order = self.env["sale.order"].create(
                    self._order_vals(self.company_a, tags)
                )
                self.assertEqual(order.tag_ids, tags)
        with self.assertRaises(UserError):
            self.env["sale.order"].create(self._order_vals(self.company_a, self.tag_b))

    def test_order_tag_company_check_multi(self):
        orders = self.env["sale.order"].create(
            [
                self._order_vals(self.company_a),
                self._order_vals(self.company_b),
            ]
        )
        orders.tag_ids = [Command.link(self.tag_shared.id)]
        self.assertEqual(orders.tag_ids, self.tag_shared)
        with self.assertRaises(UserError):
            orders[0].tag_ids = [Command.link(self.tag_b.id)]
        with self.assertRaises(UserError):
            self.env["sale.order"].create(
                [
                    self._order_vals(self.company_b, self.tag_b),
                    self._order_vals(self.company_a, self.tag_b),
                ]
            )

    def test_order_change_company(self):
        orders = self.env["sale.order"].create(
            [
                self._order_vals(self.company_a, self.tag_shared),
                self._order_vals(self.company_a, self.tag_a),
            ]
        )
        orders[0].company_id = self.company_b
        self.assertEqual(orders[0].tag_ids, self.tag_shared)
        with self.assertRaises(UserError):
            orders[1].company_id = self.company_b

    def test_order_form_quick_create_tag(self):
        arch = self.env["sale.order"].get_view(view_type="form")["arch"]
        node = etree.fromstring(arch).xpath("//field[@name='tag_ids']")[0]
        ctx = safe_eval(node.get("context"), {"company_id": self.company_b.id})
        tag_id, _name = self.env["crm.tag"].with_context(**ctx).name_create("Quick Tag")
        order = self.env["sale.order"].create(
            self._order_vals(self.company_b, self.env["crm.tag"].browse(tag_id))
        )
        self.assertEqual(order.tag_ids.company_id, self.company_b)
