# © 2023 David BEAL @ Akretion
# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, tests

from odoo.addons.base.tests.common import BaseCommon


@tests.tagged("-at_install", "post_install")
class Test(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_view = cls.env.ref("base.view_partner_form")
        cls.partner_view.inherit_children_ids = [
            fields.Command.create(
                {
                    "name": "Test view to include a company dependent field",
                    "model": "res.partner",
                    "arch": """
<field name="vat" position="after">
    <field name="barcode" />
</field>
            """,
                }
            )
        ]

    def test_class_company(self):
        arch, view = self.env["res.partner"]._get_view(view_id=self.partner_view.id)
        for field in arch.xpath("//field[@name='barcode']"):
            self.assertIn("building", field.attrib.get("data-company-dep-class"))
            break
        else:
            self.fail("Barcode field not found in the view")
