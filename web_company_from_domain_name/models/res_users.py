# -*- coding: utf-8 -*-
# Copyright 2019 AppsToGROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, exceptions, fields, models, tools
from odoo.http import request


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    @tools.ormcache('uid')
    def get_cached_domain_name(cls, uid, current_domain_name):
        return current_domain_name

    def _inverse_company_id(self):
        """ Save selected company id to stored_company_id """
        for this in self:
            this.stored_company_id = this.company_id

    def _compute_company_id(self):
        """ Change company_id on user to a computed field based on URL """
        company_obj = self.env['res.company']
        company_id = self.env.context.get('force_company', None)
        company = company_id and company_obj.browse(company_id)
        if request and not company:
            url_domain = request.httprequest.host.partition(":")[0]
            company = company_obj.search([
                ('access_url', '=', url_domain),
                ('user_ids', 'in', self.ids)
            ])[:1]
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
