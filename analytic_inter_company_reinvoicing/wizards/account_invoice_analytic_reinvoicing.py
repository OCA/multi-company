# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoiceAnalyticReinvoicing(models.TransientModel):

    _name = 'account.invoice.analytic.reinvoicing'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        default=lambda self: self.env.user.company_id,
        required=True,
        ondelete='cascade',
    )

    @api.multi
    def get_lines_to_reinvoice_domain(self):
        self.ensure_one()
        return [
            ('invoice_id.type', '=', 'in_invoice'),
            ('invoice_id.company_id', '=', self.company_id.id),
            ('invoice_id.state', 'not in', ('draft', 'cancelled')),
            ('reinvoice_analytic_account_id', '!=', False),
            ('reinvoice_line_id', '=', False),
            ('company_id', '=', self.company_id.id),
        ]

    @api.multi
    def get_lines_to_reinvoice_by_company(self):
        self.ensure_one()
        domain = self.get_lines_to_reinvoice_domain()
        invoice_lines = self.env['account.invoice.line'].search(domain)
        invoice_lines_by_company = {}
        for invoice_line in invoice_lines:
            analytic_account = invoice_line.reinvoice_analytic_account_id
            company = analytic_account.company_id
            if company not in invoice_lines_by_company:
                invoice_lines_by_company[company] = self.env[
                    'account.invoice.line']
            invoice_lines_by_company[company] |= invoice_line
        return invoice_lines_by_company

    @api.multi
    def create_invoice_for_company(self, company, invoice_lines):
        self.ensure_one()
        invoice = self.env['account.invoice'].create(
            self.get_invoice_values(company))
        for invoice_line in invoice_lines:
            self.create_invoice_line(invoice, invoice_line)
        invoice.button_reset_taxes()
        return invoice

    @api.multi
    def get_invoice_values(self, company):
        self.ensure_one()
        partner = company.partner_id
        account = partner.property_account_receivable
        values = {
            'partner_id': company.partner_id.id,
            'currency_id': company.currency_id.id,
            'account_id': account.id,
            'type': 'out_invoice',
            'date_invoice': fields.Date.today(),
            'company_id': self.company_id.id,
        }
        return values

    @api.multi
    def get_invoice_line_values(self, invoice, original_inv_line):
        self.ensure_one()
        amount = original_inv_line.price_unit
        analytic_account = original_inv_line.reinvoice_analytic_account_id
        to_company = analytic_account.company_id
        currency = to_company.currency_id
        from_currency = original_inv_line.invoice_id.currency_id

        if currency != from_currency:
            amount = from_currency.compute(amount, currency)
        values = {
            'invoice_id': invoice.id,
            'price_unit': amount,
            'reinvoice_analytic_account_id': False,
        }
        return original_inv_line.copy_data(default=values)[0]

    @api.multi
    def create_invoice_line(self, invoice, original_inv_line):
        self.ensure_one()
        values = self.get_invoice_line_values(invoice, original_inv_line)
        inv_line = self.env['account.invoice.line'].create(values)
        original_inv_line.write({
            'reinvoice_line_id': inv_line.id,
        })
        return inv_line

    @api.multi
    def create_invoices(self):
        self.ensure_one()
        invoices = self.env['account.invoice']
        invoice_lines_by_company = self.get_lines_to_reinvoice_by_company()
        for company, invoice_lines in invoice_lines_by_company.iteritems():
            invoice = self.create_invoice_for_company(company, invoice_lines)
            invoice.signal_workflow('invoice_open')
            self.reconcile_reinvoiced_lines(invoice)
            invoices |= invoice
        return invoices

    @api.multi
    def reconcile_reinvoiced_lines(self, invoice):
        self.ensure_one()
        move = invoice.move_id
        waiting_account = invoice.company_id.reinvoice_waiting_account_id

        origin_invoice = self.env['account.invoice'].search([
            ('invoice_line.reinvoice_line_id', 'in', invoice.invoice_line.ids),
        ], limit=1)

        lines_to_reconcile = self.env['account.move.line'].search([
            ('reconcile_id', '=', False),
            ('account_id', '=', waiting_account.id),
            '|',
            ('id', 'in', move.line_id.ids),
            ('id', 'in', origin_invoice.move_id.line_id.ids),
        ])
        period = self.env['account.period'].find(
            dt=origin_invoice.date_invoice)
        lines_to_reconcile.reconcile(
            writeoff_journal_id=move.journal_id.id,
            writeoff_period_id=period and period[0].id or False,
        )

    @api.multi
    def execute(self):
        invoice_ids = []
        for wizard in self:
            invoices = wizard.with_context(
                company_id=wizard.company_id.id,
                force_company=wizard.company_id.id,
            ).create_invoices()
            invoice_ids.extend(invoices.ids)
        action = self.env.ref('account.action_invoice_tree1').read([])[0]
        action.update({
            'domain': [('id', 'in', invoice_ids)],
        })
        return action
