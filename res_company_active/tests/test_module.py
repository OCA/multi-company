# coding: utf-8
# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError


class TestModule(TransactionCase):

    def setUp(self):
        super(TestModule, self).setUp()
        self.test_company = self.env.ref('res_company_active.company_test')
        self.demo_user = self.env.ref('base.user_demo')

    # Test Section
    def test_01_disable_without_user(self):
        self.test_company.active = False

    def test_02_disable_with_user(self):
        self.demo_user.company_id = self.test_company
        with self.assertRaises(ValidationError):
            self.test_company.active = False
