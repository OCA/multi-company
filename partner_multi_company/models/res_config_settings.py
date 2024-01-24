from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    set_active_company_partner = fields.Boolean(
        string="Set Active Company Partner",
        related="company_id.set_active_company_partner",
        readonly=False,
    )
