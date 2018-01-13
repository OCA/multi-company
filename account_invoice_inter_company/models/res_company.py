# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    invoice_auto_validation = fields.Boolean(
        help="When an invoice is created by a multi company rule "
             "for this company, it will automatically validate it",
        default=True)

    @api.multi
    def _get_user_domain(self):
        self.ensure_one()
        group_account_invoice = self.env.ref('account.group_account_invoice')
        return [
            ('id', '!=', self.env.ref('base.user_root').id),
            ('company_id', '=', self.id),
            ('id', 'in', group_account_invoice.users.ids),
        ]
