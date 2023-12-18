#  Copyright 2023 Simone Rubino - Aion Tech
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.base_inherit_company.tests.common import Common


class TestPartner(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env["res.partner"]

    def test_inherit_company(self):
        """Partners created for an element of a family of companies
        are shared to all the companies"""
        # Arrange: A family of companies
        companies = self.parent_company | self.child_company | self.sibling_company

        # Act: Create a partner for each company
        partners = self.partner_model.browse()
        for company in companies:
            partner_form = Form(self.partner_model.with_company(self.parent_company))
            partner_form.name = "Partner of " + company.name
            partner_form.company_ids.clear()
            partner_form.company_ids.add(company)
            partner = partner_form.save()
            partners |= partner

        # Assert: All created partners are shared to every element of the family
        for partner in partners:
            self.assertEqual(partner.company_ids, companies)
