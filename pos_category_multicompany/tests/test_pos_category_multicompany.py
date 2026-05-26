# Copyright (C) 2013 - Today: GRAP (http://www.grap.coop)
# @author Julien WESTE
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# @author Quentin DUPONT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class TestPosCategory(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Test Company"})

    def test_default_company_id(self):
        pos_category = self.env["pos.category"].create({"name": "Test Category"})
        self.assertEqual(
            pos_category.company_id,
            self.env.company,
            "Default company should be the current company",
        )

    def test_custom_company_id(self):
        pos_category = self.env["pos.category"].create(
            {"name": "Test Category", "company_id": self.company.id}
        )
        self.assertEqual(
            pos_category.company_id, self.company, "Company ID should be set correctly"
        )
