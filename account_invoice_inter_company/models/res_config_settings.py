# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InterCompanyRulesConfig(models.TransientModel):

    _inherit = 'res.config.settings'

    invoice_auto_validation = fields.Boolean(
        related='company_id.invoice_auto_validation',
        string='Invoices Auto Validation',
        help='When an invoice is created by a multi company rule for '
             'this company, it will automatically validate it.')
    use_inter_company_products = fields.Boolean(
        related='company_id.use_inter_company_products',
        help="Use the same products when an invoice is created by "
             "a multi company rule.")
