# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    @api.constrains('user_id')
    def _check_user_id(self):
        """Do not allow same public user on two websites.s"""
        for record in self:
            existing = self.search([('user_id', '=', record.user_id.id)])
            if len(existing) > 1:
                raise ValidationError(_(
                    'You cannot assign the same public user to two websites.',
                ))

    @api.multi
    @api.constrains('user_id.company_id', 'company_id')
    def _check_user_id_company_id(self):
        """Do not allow differing company on public user and website."""
        for record in self:
            if record.company_id != record.user_id.company_id:
                raise ValidationError(_(
                    'The public user company must match the website company.',
                ))

    @api.model
    def create(self, vals):
        """Assign a unique public user per website and align the company."""
        # Assign (possibly new) user if not manually selected
        if not vals.get('user_id'):
            user = self._get_new_public_user()
            company_id = vals.get('company_id') or self.env.user.company_id.id
            if user.company_id.id != company_id:
                user.write({
                    'company_id': company_id,
                    'company_ids': [(6, 0, [company_id])],
                })
            vals['user_id'] = user.id
        # Create website
        website = super(Website, self).create(vals)
        # This is required to circumvent duplicate key on login
        user.write({
            'login': 'public-%d' % website.id,
            'name': 'Public User (Website %s)' % website.id,
        })
        return website

    @api.multi
    def write(self, vals):
        """Keep the user company synced with website & don't allow editing."""
        if vals.get('user_id') and not self.env.context.get('write_user'):
            raise ValidationError(_(
                'The website public user is maintained automatically and '
                'cannot be set.',
            ))
        if vals.get('company_id'):
            for record in self:
                if record.user_id.company_id.id != vals['company_id']:
                    record.user_id.write({
                        'company_id': vals['company_id'],
                        'company_ids': [(6, 0, [company_id])],
                    })
        return super(Website, self).write(vals)

    @api.model
    def _get_new_public_user(self):
        """Get a public user that is not assigned to a website."""
        public_user = self.env.ref('base.public_user')
        existing = self.search([('user_id', '=', public_user.id)])
        if not existing:
            return public_user
        return public_user.copy()
