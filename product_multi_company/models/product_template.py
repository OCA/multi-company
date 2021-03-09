# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = ["multi.company.abstract", "product.template"]
    _name = "product.template"
    _description = "Product Template (Multi-Company)"

    company_ids = fields.Many2many(
        compute="_compute_company_ids", inverse="_inverse_company_ids", store=True,
    )

    @api.depends("product_variant_ids.company_ids")
    def _compute_company_ids(self):
        """Set of all companies from all variants plus the template's own companies."""
        for template in self:
            companies_set = set()
            variants_companies = [
                variant.company_ids.ids for variant in template.product_variant_ids
            ]
            for companies in variants_companies:
                companies_set.update(companies)
            template.company_ids += self.env["res.company"].browse(companies_set)

    def _inverse_company_ids(self):
        """Remove companies from this template's variants which are not assigned "
        "to the template."""
        for variant in self.product_variant_ids:
            remaining_companies = list(
                set(variant.company_ids.ids).intersection(self.company_ids.ids)
            )
            variant.with_context(company_inverse=True).company_ids = [
                (6, 0, remaining_companies)
            ]
