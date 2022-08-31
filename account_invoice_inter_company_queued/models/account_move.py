from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _post(self, soft=True):
        self = self.with_context(account_invoice_inter_company_queued=True)
        res = super(AccountMove, self)._post(soft=soft)
        for src_invoice in self.filtered(lambda x: x.is_invoice()):
            dest_company = src_invoice._find_company_from_invoice_partner()
            if dest_company and not src_invoice.auto_generated:
                src_invoice.sudo().with_delay().create_counterpart_invoices()
        return res
