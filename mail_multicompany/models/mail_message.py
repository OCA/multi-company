# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class MailMessage(models.Model):

    _inherit = 'mail.message'

    company_id = fields.Many2one('res.company', 'Company')

    @api.model
    def create(self, vals):
        if not vals.get('company_id'):
            if vals.get('author_id', False):
                author_user = self.env['res.users'].search(
                    [('partner_id', '=', vals['author_id'])])
                company_id = author_user.company_id.id
            else:
                company_id = self.env.user.company_id.id
            vals['company_id'] = company_id
        if vals.get('model') and vals.get('res_id'):
            current_object = self.env[vals['model']].browse(vals['res_id'])
            if hasattr(current_object, 'company_id'):
                vals['company_id'] = current_object.company_id.id
        if not vals.get('mail_server_id'):
            vals['mail_server_id'] = self.sudo().env['ir.mail_server'].search(
                [('company_id', '=', vals.get('company_id', False))],
                order='sequence', limit=1).id
        return super(MailMessage, self).create(vals)
