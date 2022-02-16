# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    intercompany_sequence = fields.Integer(
        default=-1,
        help="Determines the order of automatically "
        "generated supplier prices for other "
        "companies. For correct behaviour, "
        "values should always be negative",
    )
