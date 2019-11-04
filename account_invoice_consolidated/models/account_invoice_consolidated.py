# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountInvoiceConsolidation(models.Model):
    _name = 'account.invoice.consolidated'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Invoice Consolidation'

    @api.depends('invoice_ids', 'invoice_ids.residual')
    def _compute_amount(self):
        for consolidated_inv in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            residual = 0.0
            for invoice in consolidated_inv.invoice_ids:
                amount_untaxed += invoice.amount_untaxed
                amount_tax += invoice.amount_tax
                residual += invoice.residual
            consolidated_inv.amount_untaxed = amount_untaxed
            consolidated_inv.amount_tax = amount_tax
            consolidated_inv.residual = residual
            consolidated_inv.amount_total = amount_untaxed + amount_tax

    name = fields.Char(readonly=True, default='Draft')
    date_from = fields.Date(required=True, readonly=True, states={
                            'draft': [('readonly', False)]})
    date_to = fields.Date(required=True, readonly=True, states={
                          'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 track_visibility='onchange',
                                 default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one('res.partner', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 track_visibility='onchange')
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  readonly=True)
    amount_untaxed = fields.Monetary(compute='_compute_amount',
                                     track_visibility='onchange', store=True)
    amount_tax = fields.Monetary(compute='_compute_amount',
                                 track_visibility='onchange', store=True)
    amount_total = fields.Monetary(compute='_compute_amount',
                                   track_visibility='onchange', store=True)
    residual = fields.Monetary(compute='_compute_amount', string="Amount Due",
                               track_visibility='onchange', store=True)
    amount_currency = fields.Monetary()
    invoice_id = fields.Many2one('account.invoice',
                                 string='Consolidated Invoice',
                                 readonly=True,
                                 states={'draft': [('readonly', False)]})
    invoice_ids = fields.Many2many('account.invoice', readonly=True,
                                   states={'draft': [('readonly', False)]})
    payment_ids = fields.One2many('account.payment', 'consolidation_id',
                                  readonly=True,
                                  states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], default='draft',
                             readonly=True, track_visibility='onchange')

    @api.constrains('name')
    def _check_name_duplication(self):
        for inv in self:
            if inv.name != 'Draft':
                if self.search_count([('name', '=', inv.name),
                                      ('id', '!=', inv.id)]):
                    raise ValidationError(
                        _("Consolidated Invoice Number must be unique!"))

    @api.constrains('partner_id', 'date_from', 'date_to')
    def _check_date_validation(self):
        for inv in self:
            if inv.date_from > inv.date_to:
                raise ValidationError(
                    _("End Date should be greater than Start Date!"))
            if inv.search_count([
                ('state', '=', 'draft'),
                ('partner_id', '=', inv.partner_id.id),
                '|', '|', '&',
                ('date_from', '<=', inv.date_from),
                ('date_to', '>=', inv.date_from), '&',
                ('date_from', '<=', inv.date_to),
                ('date_to', '>=', inv.date_to), '&',
                ('date_from', '<=', inv.date_from),
                ('date_to', '>=', inv.date_to)])\
                    > 1:
                raise ValidationError(
                    _('Draft Consolidated Invoice exists for selected '
                      'Customer/Date Range.\n Please add the invoice there.'))

    @api.onchange('partner_id', 'date_from', 'date_to')
    def _onchange_partner(self):
        if not self.partner_id or self.invoice_ids and self.partner_id and \
                self.invoice_ids[0].partner_id != self.partner_id:
            self.invoice_ids = False
        if self.date_from and self.date_to and self.partner_id:
            inv_rec = self.env['account.invoice'].search(
                [('partner_id', '=', self.partner_id.id),
                 ('date_invoice', '>=', self.date_from),
                 ('date_invoice', '<=', self.date_to),
                 ('state', '=', 'open'),
                 ('type', '=', 'out_invoice')])
            if inv_rec:
                self.invoice_ids = [(6, 0, inv_rec.ids)]

    @api.multi
    def action_confirm_invoice(self):
        for rec in self:
            if not rec.invoice_ids:
                raise ValidationError(
                    _("Add some invoices to proceed further."))
            # Validation to check Intercompany Payment Configuration
            company_ids = rec.company_id
            company_ids |= rec.invoice_ids.mapped('company_id')
            for company in company_ids:
                if not company.due_from_account_id or \
                        not company.due_to_account_id or \
                        not company.due_fromto_payment_journal_id:
                    raise ValidationError(
                        _("Intercompany Payment Configuration is missing for"
                          " %s." % (company.display_name)))
            invoice_consolidated_seq = self.env['ir.sequence'].next_by_code(
                'consolidated.invoice')
            if invoice_consolidated_seq:
                rec.write({'name': invoice_consolidated_seq})
            inv_vals = {
                'ref': rec.name,
                'partner_id': rec.partner_id.id,
                'account_id': rec.partner_id.property_account_receivable_id.id,
                'payment_term_id': rec.partner_id.property_payment_term_id.id,
                'journal_id': self.env['account.invoice'].default_get(
                    ['journal_id'])['journal_id'],
                'company_id': rec.company_id.id}
            line_ids = []
            for invoice in rec.invoice_ids:
                line_ids.append((0, 0, {
                    'name': 'A/R due to %s - Invoice %s' %
                            (invoice.company_id.partner_id.display_name,
                             invoice.number),
                    'account_id':
                        rec.company_id.due_to_account_id.id,
                    'quantity': 1,
                    'price_unit': invoice.residual,
                    'company_id': rec.company_id.id,
                }))
                # Create a payment in the children company
                payment = self.env['account.payment'].create({
                    'partner_id': rec.company_id.partner_id.id,
                    'partner_type': 'customer',
                    'amount': invoice.residual,
                    'journal_id':
                        invoice.company_id.due_fromto_payment_journal_id.id,
                    'payment_type': 'inbound',
                    'payment_method_id':
                        invoice.company_id.due_fromto_payment_journal_id.
                        inbound_payment_method_ids[0].id,
                    'payment_date': fields.Datetime.now(),
                    'communication': rec.name,
                    'consolidation_id': rec.id,
                    'company_id': invoice.company_id.id,
                    'invoice_ids': [(4, invoice.id, None)],
                })
                # Validate the payment to reconcile the invoice
                payment.action_validate_invoice_payment()

            inv_vals.update({'invoice_line_ids': line_ids})
            # Create and validate the consolidated invoice
            invoice_id = self.env['account.invoice'].with_context(
                company_id=rec.company_id.id).create(inv_vals)
            invoice_id.action_invoice_open()
            for inv in rec.invoice_ids:
                inv.consolidated_by_id = invoice_id.id
            rec.invoice_id = invoice_id.id
            rec.state = 'done'

    @api.multi
    def unlink(self):
        for inv in self:
            if inv.state != 'draft':
                raise ValidationError(
                    _("You can delete only Draft Consolidated Invoices."))
        return super().unlink()
