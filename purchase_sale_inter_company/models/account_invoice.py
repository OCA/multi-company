# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def inter_company_create_invoice(
            self, dest_company, dest_inv_type, dest_journal_type):
        res = super(AccountInvoice, self).inter_company_create_invoice(
            dest_company, dest_inv_type, dest_journal_type)
        if dest_inv_type == 'in_invoice':
            # Link intercompany purchase order with intercompany invoice
            self._link_invoice_purchase(res['dest_invoice'])
        return res

    @api.multi
    def _link_invoice_purchase(self, dest_invoice):
        self.ensure_one()
        sales = self.env['sale.order'].search([
            ('invoice_ids', '=', self.id),
            ('auto_purchase_order_id', '!=', False)])
        for sale in sales:
            purchase = sale.auto_purchase_order_id.sudo()
            purchase.invoice_ids = [(4, dest_invoice.id)]
            if dest_invoice.state not in ['draft', 'cancel']:
                        purchase.order_line.write({'invoiced': True})
            for sale_line in sale.order_line:
                purchase_line = (sale_line.auto_purchase_line_id.
                                 sudo())
                for invoice_line in dest_invoice.invoice_line:
                    if (sale_line.invoice_lines == invoice_line.
                            auto_invoice_line_id):
                        purchase_line.invoice_lines = [
                            (4, invoice_line.id)]
