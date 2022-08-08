from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _post(self, soft=True):
        self = self.with_context(account_invoice_inter_company_queued=True)
        res = super(AccountMove, self)._post(soft=soft)
        dest_company = self._find_company_from_invoice_partner()
        if dest_company and not self.auto_generated:
            self.sudo().with_delay().create_counterpart_invoices()
        return res
