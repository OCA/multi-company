# -*- coding: utf-8 -*-
# (c) 2015 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import fields, models


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    def _default_company_id(self):
        company_model = self.env['res.company']
        company_id = company_model._company_default_get('stock.production.lot')
        return company_model.browse(company_id)

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', change_default=True,
        default=_default_company_id)
