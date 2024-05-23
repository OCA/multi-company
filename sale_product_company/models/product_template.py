# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_ok_company_ids = fields.Many2many(
        "res.company",
        string="Selling Companies",
        relation="product_template_sale_product_company_company_rel",
    )

    @api.onchange("company_id")
    def _set_sale_ok_company_ids_from_company_id(self):
        self.sale_ok_company_ids = self.company_id
