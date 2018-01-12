# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    invoice_auto_validation = fields.Boolean(
        string='Invoice Auto Validation',
        help="When an invoice is created by a multi company rule "
             "for this company, it will automatically validate it",
        default=True)

    @api.model
    def _find_company_from_partner(self, partner_id):
        company = self.sudo().search([('partner_id', '=', partner_id)],
                                     limit=1)
        return company or False
