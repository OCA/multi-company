# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    company_ids = fields.Many2many(
        comodel_name="res.company",
        relation="product_pricelist_item_company_rel",
        column1="pricelist_item_id",
        column2="company_id",
        related="pricelist_id.company_ids",
        store=True,
    )
