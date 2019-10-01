# -*- coding: utf-8 -*-
# Copyright 2019 AppsToGROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import odoo
from odoo import api, exceptions, models, SUPERUSER_ID, tools
from odoo.http import request


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    @tools.ormcache('uid')
    def get_cached_domain_name(cls, uid, current_domain_name):
        """ Returns cached domain name per user """
        return current_domain_name

    @api.model
    @tools.ormcache('uid')
    def get_cached_company_id(self, uid):
        """ Returns cached company_id per user """
        company_id = self._get_company_id_from_domain_name(uid)
        return company_id

    @api.model
    def _get_company_id_from_domain_name(self, uid):
        """ Retrieve company_id through domain name """
        company_obj = self.env['res.company']
        company_id = self.env.context.get('force_company', None)
        if request and not company_id:
            domain_name = request.httprequest.host.partition(":")[0]
            company_id = company_obj.sudo().search([
                ('access_url', '=', domain_name),
                ('user_ids', 'in', [uid])
            ])[:1].id
        return company_id

    def _read_from_database(self, field_names, inherited_field_names=[]):
        """ Read with modified company_id """
        ret = super(ResUsers, self)._read_from_database(
            field_names, inherited_field_names=inherited_field_names)
        if 'company_id' in field_names:
            for this in self.filtered(lambda u: u.id != SUPERUSER_ID):
                company_id = self.get_cached_company_id(this.id)
                if company_id:
                    this._cache.update({'company_id': (company_id,)})
        return ret
