# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _default_company_ids(self):
        company_model = self.env['res.company']
        return [(6, 0,
                 [company_model._company_default_get('product.template')])]

    company_ids = fields.Many2many(
        comodel_name='res.company', string="Companies",
        default=_default_company_ids)
    company_id = fields.Many2one(
        comodel_name='res.company', compute="_compute_company_id", store=True)

    @api.multi
    @api.depends('company_ids')
    def _compute_company_id(self):
        for template in self:
            template.company_id = template.company_ids[:1]
