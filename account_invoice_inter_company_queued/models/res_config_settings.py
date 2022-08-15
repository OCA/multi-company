from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    module_account_invoice_inter_company_queued = fields.Boolean(
        "Queued Invoices Creation",
        help="This will install account_invoice_inter_company_queued",
    )
