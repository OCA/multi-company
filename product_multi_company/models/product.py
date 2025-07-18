# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = ["multi.company.abstract", "product.product"]
    _name = "product.product"

    company_ids = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
        related="product_tmpl_id.company_ids",
    )
