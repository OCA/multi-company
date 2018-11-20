# -*- coding: utf-8 -*-
from odoo import api, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def _inter_company_create_invoice(
            self, dest_company, dest_inv_type, dest_journal_type):
        res = super(AccountInvoice, self)._inter_company_create_invoice(
            dest_company, dest_inv_type, dest_journal_type)
        if dest_inv_type in ('in_invoice', 'out_refund'):
            # Link intercompany purchase order with purchase invoice created
            self._link_invoice_purchase(res['dest_invoice'])
        return res

    @api.multi
    def _link_invoice_purchase(self, dest_invoice):
        self.ensure_one()
        for dest_invoice_line in dest_invoice.invoice_line_ids:
            purchase_order_line_ids = dest_invoice_line.\
                auto_invoice_line_id.sale_line_ids.\
                mapped('auto_purchase_line_id')
            if purchase_order_line_ids:
                purchase_order_line_ids.invoice_lines = [
                    (6, 0, [dest_invoice_line.id])]
