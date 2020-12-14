from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    web_base_url_mail = fields.Char(
        string="Email Links URL",
        help="Company specific URL that will be used when possible "
        "in outgoing email links",
    )
