# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestWebsite(TransactionCase):

    def _create_company(self, name='ACME inc.'):
        company = self.env['res.company'].create({'name': name})
        self.env.user.company_ids = [(4, company.id)]
        return company

    def _create_website(self, company=None, name='Test', domain='Test',
                        user=None):
        if company is None:
            company = self._create_company()
        return self.env['website'].create({
            'name': name,
            'domain': domain,
            'user_id': user and user.id or False,
            'company_id': company.id,
        })

    def _create_user(self, login='public-test'):
        user = self.env.ref('base.public_user').copy()
        user.login = login
        return user

    def test_create_website_creates_user(self):
        """It should create a new user for the website."""
        existing_users = self.env['res.users'].search([])
        self._create_website()
        self.assertEqual(
            len(self.env['res.users'].search([])),
            len(existing_users) + 1,
        )

    def test_create_multiple_websites(self):
        """It should allow multiple website creations.

        This tests specifically for duplicate key errors on the users that
        are automatically created.
        """
        self._create_website()
        self._create_website()
        self.assertTrue(True)

    def test_create_website_prexisting_user_no_new(self):
        """It should not create a new user if defined."""
        user = self._create_user()
        existing_users = self.env['res.users'].search([])
        self._create_website(user=user)
        self.assertEqual(
            len(self.env['res.users'].search([])),
            len(existing_users),
        )

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
            website.user_id.company_id, self.env.user.company_id.id,
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
        self.website.with_context(write_user=True).user_id = user.id
        self.assertEqual(website.user_id, user)

    def test_check_user_id(self):
        """It should not allow the same user for two websites."""
        existing = self.env['website'].search([], limit=1)
        website = self._create_website()
        with self.assertRaises(ValidationError):
            website.with_context(write_user=True).user_id = \
                existing.user_id.id

    def test_check_user_id_company_id(self):
        """It should not allow mismatched company on user and website."""
        existing = self.env['website'].search([], limit=1)
        with self.assertRaises(ValidationError):
            self._create_website(company=existing.company_id)
