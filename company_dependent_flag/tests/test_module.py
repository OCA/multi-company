# © 2023 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class Test(common.TransactionCase):
    def test_class_company(self):
        fields_info = self.env["res.partner"].fields_get()
        self.assertIn(
            "building", fields_info["phone"].get("company_dependent_css_class", "")
        )
        self.assertNotIn(
            "building", fields_info["name"].get("company_dependent_css_class", "")
        )
