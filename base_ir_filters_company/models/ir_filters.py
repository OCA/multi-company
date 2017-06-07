# -*- coding: utf-8 -*-
# © 2016  Laetitia Gangloff, Acsone SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class IrFilters(models.Model):
    _inherit = 'ir.filters'

    @api.model
    def _get_company(self):
        company_obj = self.env['res.company']
        return company_obj.browse(
            company_obj._company_default_get('ir.filters')).id

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=_get_company)
