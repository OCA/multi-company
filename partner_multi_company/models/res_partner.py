# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html.html

from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _default_company_ids(self):
        company_model = self.env['res.company']
        return [(6, 0,
                 [company_model._company_default_get('res.partner')])]

    company_ids = fields.Many2many(
        comodel_name='res.company', string="Companies",
        default=_default_company_ids)
    company_id = fields.Many2one(
        comodel_name='res.company', compute="_compute_company_id", store=True)

    @api.depends('company_ids')
    def _compute_company_id(self):
        for partner in self:
            partner.company_id = partner.company_ids[:1]
