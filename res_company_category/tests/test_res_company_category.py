# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class TestResCompanyCategory(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.category_view = cls.env["res.company.category"].create(
            {
                "name": "Parent Category",
                "type": "view",
            }
        )

        cls.category_normal = cls.env["res.company.category"].create(
            {
                "name": "Normal Category",
                "type": "normal",
                "parent_id": cls.category_view.id,
            }
        )

        cls.company = cls.env["res.company"].create(
            {
                "name": "Test Company",
                "category_id": cls.category_normal.id,
            }
        )

    def test_company_category_assignment(self):
        """Test that a company is correctly assigned to a category"""
        self.assertEqual(self.company.category_id, self.category_normal)

    def test_category_hierarchy(self):
        """Test category hierarchy and computed fields"""
        self.assertEqual(self.category_normal.parent_id, self.category_view)
        self.assertIn(self.category_normal, self.category_view.child_ids)

    def test_category_company_qty(self):
        """Test that company quantity is correctly computed"""
        self.category_normal._compute_company_qty()
        self.assertEqual(self.category_normal.company_qty, 1)

        self.category_view._compute_company_qty()
        self.assertEqual(self.category_view.company_qty, 1)
