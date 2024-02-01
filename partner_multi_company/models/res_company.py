from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    set_active_company_partner = fields.Boolean(
        "Set Active Company Partner", default=False
    )
