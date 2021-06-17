from odoo import models


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def get_invoice_line_account(self, type, product, fpos, company):
        res = super().get_invoice_line_account(type, product, fpos, company)
        if type in ('out_invoice', 'out_refund'):
            partner = self.invoice_id.partner_id.id
        else:
            partner = self.partner_id.id
        is_intercompany = self.env['res.company'].search(
            [('partner_id', '=', partner)]
        )
        if is_intercompany:
            inter_company_accounts = product.product_tmpl_id.\
                get_product_intercompany_accounts()
            if type in ('out_invoice', 'out_refund'):
                res = inter_company_accounts["income"] or res
            else:
                res = inter_company_accounts["expense"] or res
        return res
