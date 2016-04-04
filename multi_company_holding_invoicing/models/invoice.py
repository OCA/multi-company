# -*- coding: utf-8 -*-
# © 2015 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    company_sale_ids = fields.One2many('sale.order', 'holding_company_id')
    holding_sale_ids = fields.One2many('sale.order', 'holding_invoice_id')
    holding_sale_count = fields.Integer(
        compute='_holding_sale_count', string='# of Sales Order')
    sale_count = fields.Integer(
        compute='_sale_count', string='# of Sales Order')
    child_invoice_ids = fields.One2many(
        'account.invoice', 'holding_invoice_id')
    child_invoice_count = fields.Integer(
        compute='_child_invoice_count', string='# of Invoice')
    holding_invoice_id = fields.Many2one('account.invoice', 'Holding Invoice')

    @api.multi
    def _holding_sale_count(self):
        for inv in self:
            inv.holding_sale_count = len(inv.holding_sale_ids)

    @api.multi
    def _sale_count(self):
        for inv in self:
            inv.sale_count = len(inv.sale_ids)

    @api.multi
    def _child_invoice_count(self):
        for inv in self:
            inv.child_invoice_count = len(inv.child_invoice_ids)

    @api.multi
    def unlink(self):
        sale_obj = self.env['sale.order']
        sales = sale_obj.search([('holding_invoice_id', 'in', self.ids)])
        res = super(AccountInvoice, self).unlink()
        # We use an SQL request here for solving perf issue
        if sales:
            self._cr.execute("""UPDATE sale_order
                SET invoice_state = 'invoiceable'
                WHERE id in %s""", (tuple(sales.ids),))
        return res

    @api.multi
    def generate_child_invoice(self):
        invoices = self.browse(False)
        for company in self.env['res.company'].search([]):
            sales = self.env['sale.order']\
                .suspend_security()\
                .with_context(force_company=company.id, from_holding=True)\
                .search([
                    ('holding_invoice_id', '=', self.id),
                    ('company_id', '=', company.id),
                    ])
            if sales:
                invoices |= sales.action_child_invoice()
                # Dummy call to workflow, will not create another invoice
                # but bind the new invoice to the subflow
                sales.signal_workflow('manual_invoice')
        for invoice in invoices:
            invoice.signal_workflow('invoice_open')
        return True


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sale_line_ids = fields.Many2many(
        comodel_name='account.invoice.line',
        relation='sale_order_line_invoice_rel',
        column1='invoice_id',
        column2='order_line_id')
