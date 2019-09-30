# -*- coding: utf-8 -*-
# Copyright 2019 AppsToGROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models, SUPERUSER_ID, tools
from odoo.http import request
from odoo.tools import mute_logger

from psycopg2 import ProgrammingError

import logging
_logger = logging.getLogger(__name__)

import odoo.sql_db


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _inverse_company_id(self):
        """ Save selected company id to stored_company_id """
        for this in self:
            this.stored_company_id = this.company_id

    def _compute_company_id(self):
        """ Change company_id on user to a computed field based on URL """
        company_obj = self.env['res.company']
        company_id = self.env.context.get('force_company', None)
        company = company_id and company_obj.browse(company_id)
        if not company:
            try:
                url_domain = request.httprequest.host.partition(":")[0]
                company = company_obj.search([
                    ('access_url', '=', url_domain)
                ])[:1] & self.env.user.company_ids
            except RuntimeError:
                company = None
        for this in self:
            this.company_id = \
                company or this.stored_company_id or this.company_ids[:1]

    company_id = fields.Many2one(
        compute='_compute_company_id',
        inverse='_inverse_company_id',
        string='Company (from URL)',
        store=False, index=False, required=False)
    stored_company_id = fields.Many2one(
        'res.company', string='Company (stored)', readonly=True)

    ''' PORTAL USER - rather use 'share' field... '''

    #def _compute_is_portal_user(self):
    #    for record in self:
    #        record.is_portal_user = record.has_group('base.group_portal')
    #
    #is_portal_user = fields.Boolean('Is portal user', compute='_compute_is_portal_user')


    ''' CONTEXT WITH COMPANY_ID '''

    # # source: /base/res/res_users.py
    # @api.model
    # @tools.ormcache('self.env.uid', 'self.env.context.get("company_id")') #UPDATED
    # def context_get(self):
    #     user = self.env.user
    #     result = {}
    #     for k in self._fields:
    #         if k.startswith('context_'):
    #             context_key = k[8:]
    #         elif k in ['company_id', 'lang', 'tz']: #UPDATED
    #             context_key = k
    #         else:
    #             context_key = False
    #         if context_key:
    #             res = getattr(user, k) or False
    #             if isinstance(res, models.BaseModel):
    #                 res = res.id
    #             result[context_key] = res or False
    #     return result

    # # source: /base/res/res_users.py
    # @api.multi
    # @api.constrains('company_id', 'company_ids')
    # def _check_company(self):
    #     #if any(user.company_ids and user.company_id not in user.company_ids for user in self):
    #     #    raise ValidationError(_('The chosen company is not in the allowed companies for this user'))
    #     pass
