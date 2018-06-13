# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class MailMessage(models.Model):

    _inherit = 'mail.message'

    company_id = fields.Many2one('res.company', 'Company')

    @api.model
    def create(self, vals):
        if not vals.get('company_id') and vals['author_id']:
            author_user = self.env['res.users'].search(
                [('partner_id', '=', vals['author_id'])])
            vals['company_id'] = author_user.company_id.id
        if vals.get('model') and vals.get('res_id'):
            object = self.env[vals['model']].browse(vals['res_id'])
            if 'company_id' in object._fields:
                vals['company_id'] = object.company_id.id
        if not vals.get('mail_server_id'):
            vals['mail_server_id'] = self.sudo().env['ir.mail_server'].search(
                [('company_id', '=', vals.get('company_id', False))]).id
        return super(MailMessage, self).create(vals)
