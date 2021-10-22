# Copyright (C) 2021 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase


class TestPartnerContactCompanyPropagation(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test main partner", "company_id": cls.company.id}
        )

    def test_children_commercial_field(self):
        children = self.env["res.partner"].create(
            {"name": "Test children", "parent_id": self.partner.id}
        )
        self.assertEqual(children.company_id, self.partner.company_id)

        self.partner.company_id = None
        self.assertFalse(children.company_id)
