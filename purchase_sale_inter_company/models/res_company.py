# -*- coding: utf-8 -*-
from openerp import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    sale_auto_validation = fields.Boolean(
        string='Sale Auto Validation',
        help="When a Sale Order is created by a multi company rule "
             "for this company, it will automatically validate it",
        default=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse For Sale Orders',
        help="Default value to set on Sale Orders that "
        "will be created based on Purchase Orders made to this company")
