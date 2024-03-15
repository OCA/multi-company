# © 2023 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import xml.dom.minidom as minidom

from odoo.tests import common


class Test(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner_view = cls.env.ref("base.view_partner_form")

    def test_class_company(self):
        res = self.env["res.partner"]._fields_view_get(view_id=self.partner_view.id)
        arch = minidom.parseString(res["arch"])
        for field in arch.getElementsByTagName("field"):
            if field.getAttribute("name") == "phone":
                parent = field.parentNode
                # Check if the parent is a div and contains a span
                if parent.tagName == "div" and parent.firstChild.tagName == "span":
                    # Check if the span contains the building icon
                    self.assertEqual(
                        parent.firstChild.getAttribute("class"),
                        "fa fa-lg fa-building-o",
                    )
