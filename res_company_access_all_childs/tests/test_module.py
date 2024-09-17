# Copyright (C) 2024 - Today: GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestModule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ResUsers = cls.env["res.users"]
        cls.ResCompany = cls.env["res.company"]
        cls.user_demo = cls.env.ref("base.user_demo")
        cls.base_company = cls.env.ref("base.main_company")
        cls.parent_company = cls.ResCompany.create(
            {
                "name": "Parent Company",
            }
        )
        cls.child_company = cls.ResCompany.create(
            {
                "name": "Child Company",
                "parent_id": cls.parent_company.id,
            }
        )

    # Test Section
    def test_01_res_users_propagate_access_right_create(self):
        """[Functional Test] A new user with access to mother company must
        have access to child companies"""
        new_user = self.ResUsers.create(
            {
                "name": "new_user",
                "login": "new_user@odoo.com",
                "company_id": self.parent_company.id,
                "company_ids": [(4, self.parent_company.id)],
            }
        )
        self.assertIn(
            self.child_company.id,
            new_user.company_ids.ids,
            "Affect a parent company to a new user must give access right"
            "to the childs companies",
        )

    def test_02_res_users_propagate_access_right_write(self):
        """[Functional Test] Give access to a mother company must give acces
        to the child companies"""
        new_user = self.ResUsers.create(
            {
                "name": "new_user",
                "login": "new_user@odoo.com",
                "company_id": self.base_company.id,
                "company_ids": [(4, self.base_company.id)],
            }
        )
        new_user.write({"company_ids": [(4, self.parent_company.id)]})
        self.assertIn(
            self.child_company.id,
            new_user.company_ids.ids,
            "Give access to a mother company must give access to the child companies",
        )

    def test_03_res_company_create_child_propagate_success(self):
        """[Function Test] Create a child company and check propagation."""
        new_child_company = self.ResCompany.create(
            {
                "name": "new_child_company",
                "parent_id": self.base_company.id,
            }
        )
        self.assertIn(
            new_child_company.id,
            self.user_demo.company_ids.ids,
            "Existing user must have access to the new child company.",
        )

    def test_04_res_company_write_child_propagate_success(self):
        """[Function Test] Set a company as a child company and check propagation."""
        new_child_company = self.ResCompany.create(
            {
                "name": "new_child_company",
            }
        )
        new_child_company.parent_id = (self.base_company.id,)
        self.assertIn(
            new_child_company.id,
            self.user_demo.company_ids.ids,
            "Existing user must have access to the company that is now a child company.",
        )
