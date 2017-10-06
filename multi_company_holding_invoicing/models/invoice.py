# -*- coding: utf-8 -*-
# © 2015 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job
import logging
_logger = logging.getLogger(__name__)


@job
def generate_child_invoice_job(session, model_name, args):
    invoice = session.env['account.invoice'].browse(args.get('invoice_id'))
    domain = [
        ('company_id', '=', args.get('company_id')),
        ('id', 'in', invoice.holding_sale_ids.ids)
    ]
    child_invoices = session.env['child.invoicing']._generate_invoice(domain)
    child_invoices.write({'holding_invoice_id': args.get('invoice_id')})
    for child_invoice in child_invoices:
        child_invoice.signal_workflow('invoice_open')
    return True


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    holding_sale_ids = fields.One2many('sale.order', 'holding_invoice_id')
    holding_sale_count = fields.Integer(
        compute='_compute_holding_sale_count',
        string='# of Sales Order',
        compute_sudo=True)
    sale_count = fields.Integer(
        compute='_compute_sale_count',
        string='# of Sales Order',
        compute_sudo=True)
    child_invoice_ids = fields.One2many(
        'account.invoice', 'holding_invoice_id')
    child_invoice_count = fields.Integer(
        compute='_compute_child_invoice_count',
        string='# of Invoice',
        compute_sudo=True)
    holding_invoice_id = fields.Many2one('account.invoice', 'Holding Invoice')
    child_invoice_job_ids = fields.One2many('queue.job', 'holding_invoice_id')
    child_invoice_job_count = fields.Integer(
        compute='_compute_child_invoice_job_count',
        string='# of Child Invoice Jobs')

    @api.multi
    def _compute_holding_sale_count(self):
        for inv in self:
            inv.holding_sale_count = len(inv.holding_sale_ids)

    @api.multi
    def _compute_sale_count(self):
        for inv in self:
            inv.sale_count = len(inv.sale_ids)

    @api.multi
    def _compute_child_invoice_count(self):
        for inv in self:
            inv.child_invoice_count = len(inv.sudo().child_invoice_ids)

    @api.multi
    def _compute_child_invoice_job_count(self):
        for inv in self:
            inv.child_invoice_job_count = len(inv.sudo().child_invoice_job_ids)

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            if invoice.holding_sale_ids and invoice.user_id.id == self._uid:
                invoice = invoice.suspend_security()
            invoice.holding_sale_ids._set_invoice_state('invoiced')
            super(AccountInvoice, self).invoice_validate()
        return True

    @api.multi
    def unlink(self):
        # Give some extra right to the user who have generated
        # the holding invoice
        for invoice in self:
            if invoice.holding_sale_ids and invoice.user_id.id == self._uid:
                invoice = invoice.suspend_security()
            sale_obj = self.env['sale.order']
            sales = sale_obj.search([('holding_invoice_id', '=', invoice.id)])
            super(AccountInvoice, invoice).unlink()
            sales._set_invoice_state('invoiceable')
        return True

    @api.multi
    def generate_child_invoice(self):
        # TODO add a group and check it
        self = self.suspend_security()
        session = ConnectorSession(self.env.cr, self.env.uid, self.env.context)
        for invoice in self:
            if invoice.child_invoice_ids:
                raise UserError(_(
                    'The child invoices have been already '
                    'generated for this invoice'))
            sale_companies = self.env['sale.order'].read_group([
                ('id', 'in', self.holding_sale_ids.ids),
                ('company_id', '!=', self.company_id.id),
            ], 'company_id', 'company_id')
            for sale_company in sale_companies:
                company_child_invoices = self.env['account.invoice'].search([
                    ('company_id', '=', sale_company['company_id'][0]),
                    ('holding_invoice_id', '=', invoice.id)
                ])
                if company_child_invoices:
                    break
                description = (
                    _('Generate child invoices for the company: %s') %
                    sale_company['company_id'][1])
                job_uuid = generate_child_invoice_job.delay(
                    session, self._name, {
                        'invoice_id': invoice.id,
                        'company_id': sale_company['company_id'][0]},
                    description=description)
                job = self.env['queue.job'].search(
                    [('uuid', '=', job_uuid)], limit=1)
                job.write({'holding_invoice_id': invoice.id})
        return True


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sale_line_ids = fields.Many2many(
        comodel_name='sale.order.line',
        relation='sale_order_line_invoice_rel',
        column1='invoice_id',
        column2='order_line_id')
