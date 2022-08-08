from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        use_job = self.env["ir.module.module"].search(
            [
                ("name", "=", "account_invoice_inter_company_queued"),
                ("state", "=", "installed"),
            ]
        )
        if len(use_job) == 1:
            self.sudo().with_delay().create_counterpart_invoices()
        return res
