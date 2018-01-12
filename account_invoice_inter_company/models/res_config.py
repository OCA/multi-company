# -*- coding: utf-8 -*-
from odoo import models, fields


class InterCompanyRulesAccountConfig(models.TransientModel):

    _inherit = 'account.config.settings'

    invoice_auto_validation = fields.Boolean(
        related='company_id.invoice_auto_validation',
        string='Invoices Auto Validation',
        help='When an invoice is created by a multi company rule for '
             'this company, it will automatically validate it.')
