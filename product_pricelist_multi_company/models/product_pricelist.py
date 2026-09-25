# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    company_ids = fields.Many2many(
        comodel_name="res.company",
        relation="product_pricelist_company_rel",
        column1="pricelist_id",
        column2="company_id",
        string="Available in Companies",
        compute="_compute_company_ids",
        store=True,
        readonly=False,
    )

    @api.depends("company_id")
    def _compute_company_ids(self):
        for pricelist in self:
            if not pricelist.company_id:
                pricelist.company_ids = [fields.Command.clear()]
            elif pricelist.company_id not in pricelist.company_ids:
                pricelist.company_ids = pricelist.company_ids | pricelist.company_id

    def _check_company_domain(self, companies):
        domain = super()._check_company_domain(companies)
        if not companies:
            return domain
        if isinstance(companies, str):
            return fields.Domain(domain) | fields.Domain(
                [("company_ids", "in", companies)]
            )
        if hasattr(companies, "ids"):
            company_ids = companies.ids
        elif isinstance(companies, int):
            company_ids = [companies]
        else:
            company_ids = [c for c in companies if c]
        return fields.Domain(domain) | fields.Domain(
            [("company_ids", "in", company_ids)]
        )

    def _get_partner_pricelist_multi_search_domain_hook(self, company_id):
        domain = super()._get_partner_pricelist_multi_search_domain_hook(company_id)
        return fields.Domain(domain) | fields.Domain(
            [("company_ids", "in", [company_id])]
        )
