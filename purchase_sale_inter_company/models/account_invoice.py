# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models


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
        orders = self.env['purchase.order']
        vals = {}
        if dest_invoice.state not in ['draft', 'cancel']:
            vals['invoiced'] = True
        for line in dest_invoice.invoice_line_ids:
            vals['invoice_lines'] = [(4, line.id)]
            purchase_lines = line.auto_invoice_line_id.sale_line_ids.mapped(
                'auto_purchase_line_id')
            if not purchase_lines:
                # the case where PO is generated from SO
                purchase_lines = self.env["purchase.order.line"].search([(
                    "auto_sale_line_id", "in",
                    line.auto_invoice_line_id.sale_line_ids.ids
                )])
            purchase_lines.update(vals)
            orders |= purchase_lines.mapped('order_id')
        if orders:
            ref = '<a href=# data-oe-model=purchase.order data-oe-id={}>{}</a>'
            message = _('This vendor bill is related with: {}'.format(
                ','.join([ref.format(o.id, o.name) for o in orders])))
            dest_invoice.message_post(body=message)
