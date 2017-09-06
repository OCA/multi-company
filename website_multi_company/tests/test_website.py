# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import ValidationError
from .common import Common


class TestWebsite(Common):

    def test_create_website_creates_user(self):
        """It should create a new user for the website."""
        existing_users = self.env['res.users'].search([])
        website = self._create_website()
        self.assertNotIn(website.user_id, existing_users)

    def test_create_multiple_websites(self):
        """It should allow multiple website creations.

        This tests specifically for duplicate key errors on the users that
        are automatically created.
        """
        self._create_website()
        company = self._create_company('Test Co')
        self._create_website(company, 'Test2', 'Test2')
        self.assertTrue(True)

    def test_create_website_prexisting_user_assign(self):
        """It should assign the proper user during website creation."""
        user = self._create_user()
        website = self._create_website(user=user)
        self.assertEqual(
            website.user_id,
            user,
        )

    def test_write_updates_user_company(self):
        """It should update the user company with the website."""
        website = self._create_website()
        self.assertEqual(
            website.company_id, website.user_id.company_id,
        )
        website.company_id = self.env.user.company_id.id
        self.assertEqual(
            website.user_id.company_id, self.env.user.company_id,
        )

    def test_write_no_user(self):
        """It should not allow a user to be defined when writing."""
        website = self._create_website()
        with self.assertRaises(ValidationError):
            website.user_id = self._create_user().id

    def test_write_context(self):
        """It should allow the user to be written with the right context."""
        website = self._create_website()
        user = self._create_user()
        website.with_context(write_user=True).user_id = user.id
        self.assertEqual(website.user_id, user)

    def test_check_user_id(self):
        """It should not allow the same user for two websites."""
        existing = self.env['website'].search([], limit=1)
        website = self._create_website()
        with self.assertRaises(ValidationError):
            website.with_context(write_user=True).user_id = \
                existing.user_id.id
