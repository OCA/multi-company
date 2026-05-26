# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set tracking_disable in context
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.test_company = cls.env.ref("res_company_active.company_test")
        cls.main_company = cls.env.ref("base.main_company")
        cls.demo_user = cls.env.ref("base.user_demo")

    # Test Section
    def test_01_disable_without_user(self):
        self.test_company.active = False

    def test_02_disable_with_user(self):
        self.demo_user.company_id = self.test_company
        with self.assertRaises(ValidationError):
            self.test_company.active = False

    def test_03_disable_current_company(self):
        with self.assertRaises(ValidationError):
            self.main_company.active = False
