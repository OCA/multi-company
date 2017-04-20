# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class InterCompanyRulesConfig(models.TransientModel):

    _inherit = 'base.config.settings'

    sale_auto_validation = fields.Boolean(
        string='Sale Orders Auto Validation',
        help='When a Sale Order is created by a multi company rule for '
             'this company, it will automatically validate it.')
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse For Sale Orders',
        help='Default value to set on Sale Orders that will be created '
        'based on Purchase Orders made to this company.')

    @api.onchange('company_id')
    def onchange_po_so_company_id(self):
        if self.company_id:
            self.sale_auto_validation = self.company_id.sale_auto_validation
            self.warehouse_id = self.company_id.warehouse_id.id

    @api.multi
    def set_po_so_inter_company_configuration(self):
        if self.company_id:
            vals = {
                'sale_auto_validation': self.sale_auto_validation,
                'warehouse_id': self.warehouse_id.id
            }
            self.company_id.write(vals)
