# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.http import request

from .common import Common


class TestResUsers(Common):

    def test_signup_create_user(self):
        website = self._create_website()
        request.website = website
        user = self.env['res.users']._signup_create_user({
            'name': 'TestUser',
        })
        self.assertEqual(
            user.company_id,
            website.company_id,
        )
