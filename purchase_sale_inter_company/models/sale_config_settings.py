# -*- coding: utf-8 -*-
from odoo import models, fields


class InterCompanyRulesSaleConfig(models.TransientModel):

    _inherit = 'sale.config.settings'

    sale_auto_validation = fields.Boolean(
        related='company_id.sale_auto_validation',
        string='Sale Orders Auto Validation',
        help='When a Sale Order is created by a multi company rule for '
             'this company, it will automatically validate it.')
    warehouse_id = fields.Many2one(
        related='company_id.warehouse_id',
        string='Warehouse For Sale Orders',
        help='Default value to set on Sale Orders that will be created '
        'based on Purchase Orders made to this company.')
