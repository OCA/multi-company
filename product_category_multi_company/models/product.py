# Copyright 2022 INVITU SARL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        ondelete="set null",
    )
