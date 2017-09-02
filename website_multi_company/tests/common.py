# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests import TransactionCase


class Common(TransactionCase):

    def _create_company(self, name='ACME inc.'):
        company = self.env['res.company'].create({'name': name})
        self.env.user.write({
            'company_ids': [(4, company.id)],
            'company_id': company.id,
        })
        return company

    def _create_website(self, company=None, name='Test', domain='Test',
                        user=None):
        if company is None:
            company = self._create_company()
            if user:
                user.company_ids = [(4, company.id)]
                user.company_id = company.id
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
