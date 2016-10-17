# -*- coding: utf-8 -*-
from openerp import models, fields, api


class InterCompanyRulesConfig(models.TransientModel):

    _inherit = 'base.config.settings'

    company_id = fields.Many2one(
        'res.company', string='Select Company',
        help='Select company to setup Inter company rules.')
    sale_auto_validation = fields.Boolean(
        string='Sale Orders Auto Validation',
        help='When a Sale Order is created by a multi company rule for '
             'this company, it will automatically validate it.')

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.sale_auto_validation = self.company_id.sale_auto_validation

    @api.multi
    def set_inter_company_configuration(self):
        if self.company_id:
            vals = {
                'sale_auto_validation': self.auto_validation,
            }
            self.company_id.write(vals)
