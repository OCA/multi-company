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
        for field in arch.getElementsByTagName("phone"):
            self.assertIn("building", field.getAttribute("class"))
