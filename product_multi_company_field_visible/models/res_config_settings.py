# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    multi_company_field_visible_product = fields.Boolean(
        string="Own company on products",
        help="Let users without multi-company access see and set their own "
        "company on products.",
        config_parameter="multi_company_field_visible.product",
        default=True,
    )
