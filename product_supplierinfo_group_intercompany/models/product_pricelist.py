# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    supplier_sequence = fields.Integer(
        default=-1,
        help=(
            "Force the supplier sequence, use a negative value if you want to "
            "have this supplier in first position, use a big positif value "
            "if you want to be the last"
        ),
    )
