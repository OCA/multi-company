# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = ["multi.company.abstract", "product.template"]
    _name = "product.template"

    visible_company_ids = fields.Many2many(
        comodel_name="res.company",
        compute="_compute_visible_company_ids",
        inverse="_inverse_visible_company_ids",
        string="Visible Companies",
    )

    @api.depends("company_ids")
    def _compute_visible_company_ids(self):
        for record in self:
            # Use sudo() to safely read all linked companies,
            # then filter down to only the ones in the user's current environment
            record.visible_company_ids = record.sudo().company_ids.filtered(
                lambda c: c.id in self.env.companies.ids
            )

    def _inverse_visible_company_ids(self):
        for record in self:
            # Preserve any restricted companies the user isn't allowed to see,
            # then merge them with the new selection from the UI
            hidden_companies = record.sudo().company_ids.filtered(
                lambda c: c.id not in self.env.companies.ids
            )
            record.company_ids = hidden_companies | record.visible_company_ids
