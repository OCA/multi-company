from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_tax_man_mapping = fields.Boolean(
        "Taxes Manual Mapping",
        implied_group="product_tax_multicompany_default.tax_man_mapping",
    )
