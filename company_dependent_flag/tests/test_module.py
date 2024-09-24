# © 2023 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class Test(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner_view = cls.env.ref("base.view_partner_form")

    def test_class_company(self):
        arch, view = self.env["res.partner"]._get_view(view_id=self.partner_view.id)
        for field in arch.xpath("//field[@name='phone']"):
            self.assertIn("building", field.attrib.get("class"))
