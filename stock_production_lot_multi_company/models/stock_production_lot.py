# (c) 2015 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    def _default_company_id(self):
        company_model = self.env['res.company']
        return company_model._company_default_get('stock.production.lot')

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', change_default=True,
        default=_default_company_id)

    _sql_constraints = [
        ('name_ref_uniq',
         'unique (name, product_id, company_id)',
         'The combination of serial number, product and company '
         'must be unique!'),
    ]
