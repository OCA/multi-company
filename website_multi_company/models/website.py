# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    @api.constrains('user_id')
    def _check_user_id(self):
        for record in self:
            existing = self.search([('user_id', '=', record.user_id.id)])
            if len(existing) > 1:
                raise ValidationError(_(
                    'You cannot assign the same public user to two websites.',
                ))

    @api.model
    def create(self, vals):
        if not vals.get('user_id'):
            user = self._get_public_user()
            company_id = vals.get('company_id') or self.env.user.company_id.id
            if user.company_id.id != company_id:
                user.company_id = company_id
            vals['user_id'] = user.id
        return super(Website, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('user_id') and not self.env.context.get('write_user'):
            raise ValidationError(_(
                'The website public user is maintained automatically and '
                'cannot be set.',
            ))
        if vals.get('company_id'):
            for record in self:
                if record.user_id.company_id.id != vals['company_id']:
                    record.user_id.company_id = vals['company_id']
        res = super(Website, self).write(vals)
        return res

    @api.model
    def _get_public_user(self):
        public_user = self.env.ref('base.public_user')
        existing = self.search([('user_id', '=', public_user.id)])
        if not existing:
            return public_user
        return public_user.copy()
