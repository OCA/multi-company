# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    company_ids = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
        relation="product_variant_companies_rel",
        compute="_compute_company_ids",
        store=True,
    )

    @api.depends("product_tmpl_id.company_ids")
    def _compute_company_ids(self):
        for rec in self:
            rec.company_ids = [(6, 0, rec.product_tmpl_id.company_ids.ids)]
