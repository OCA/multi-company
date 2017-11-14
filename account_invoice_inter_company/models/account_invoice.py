# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
from openerp.tools import float_compare


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    auto_generated = fields.Boolean(string='Auto Generated Document',
                                    copy=False, default=False)
    auto_invoice_id = fields.Many2one('account.invoice',
                                      string='Source Invoice',
                                      readonly=True, copy=False,
                                      _prefetch=False)

    @api.multi
    def invoice_validate(self):
        """ Validated invoice generate cross invoice base on company rules """
        for src_invoice in self:
            # do not consider invoices that have already been auto-generated,
            # nor the invoices that were already validated in the past
            dest_company = self.env['res.company']._find_company_from_partner(
                src_invoice.partner_id.id)
            if dest_company and not src_invoice.auto_generated:
                if src_invoice.type == 'out_invoice':
                    dest_inv_type = 'in_invoice'
                    dest_journal_type = 'purchase'
                elif src_invoice.type == 'in_invoice':
                    dest_inv_type = 'out_invoice'
                    dest_journal_type = 'sale'
                elif src_invoice.type == 'out_refund':
                    dest_inv_type = 'in_refund'
                    dest_journal_type = 'purchase_refund'
                elif src_invoice.type == 'in_refund':
                    dest_inv_type = 'out_refund'
                    dest_journal_type = 'sale_refund'
                src_invoice.sudo().\
                    with_context(force_company=dest_company.id).\
                    _inter_company_create_invoice(dest_company.id,
                                                  dest_inv_type,
                                                  dest_journal_type)
        return super(AccountInvoice, self).invoice_validate()

    @api.multi
    def _get_user_domain(self, dest_company):
        self.ensure_one()
        group_account_invoice = self.env.ref('account.group_account_invoice')
        return [
            ('id', '!=', 1),
            ('company_id', '=', dest_company.id),
            ('id', 'in', group_account_invoice.users.ids),
        ]

    @api.multi
    def _check_intercompany_product(self, dest_company):
        domain = self._get_user_domain(dest_company)
        dest_user = self.env['res.users'].search(domain, limit=1)
        if dest_user:
            for line in self.invoice_line:
                try:
                    line.product_id.sudo(dest_user).read(['default_code'])
                except:
                    raise UserError(_(
                        "You cannot create invoice in company '%s' with "
                        "product '%s' because it is not multicompany")
                        % (dest_company.name, line.product_id.name))

    @api.multi
    def _inter_company_create_invoice(
            self, dest_company_id, dest_inv_type, dest_journal_type):
        """ create an invoice for the given company : it will copy "
        "the invoice lines in the new invoice.
            :param dest_company : the company of the created invoice
            :rtype dest_company : res.company record
            :param dest_inv_type : the type of the invoice "
            "('in_refund', 'out_refund', 'in_invoice', ...)
            :rtype dest_inv_type : string
            :param dest_journal_type : the type of the journal "
            "to register the invoice
            :rtype dest_journal_type : string
        """
        self.ensure_one()
        dest_company = self.env['res.company'].browse(dest_company_id)
        # check intercompany product
        self._check_intercompany_product(dest_company)
        # if an invoice has already been genereted
        # delete it and force the same number
        inter_invoice = self.search([
            ('auto_invoice_id', '=', self.id),
            ('company_id', '=', dest_company_id)
        ])
        force_number = False
        if inter_invoice:
            force_number = inter_invoice.internal_number
            inter_invoice.internal_number = False
            inter_invoice.unlink()
        src_company_partner_id = self.company_id.partner_id
        dest_invoice_lines = []
        # create invoice
        dest_invoice_data = self._prepare_invoice_data(
            dest_invoice_lines, dest_inv_type,
            dest_journal_type, dest_company)
        if force_number:
            dest_invoice_data['internal_number'] = force_number
        for src_line in self.invoice_line:
            if not src_line.product_id:
                raise UserError(_(
                    "The invoice line '%s' doesn't have a product. "
                    "All invoice lines should have a product for "
                    "inter-company invoices.") % src_line.name)
            dest_inv_line_data = self._prepare_invoice_line_data(
                dest_inv_type, dest_invoice_data,
                dest_company, src_line, src_company_partner_id)
            dest_invoice_lines.append((0, 0, dest_inv_line_data))
        dest_invoice = self.create(dest_invoice_data)
        precision = self.env['decimal.precision'].precision_get('Account')
        dest_invoice.button_reset_taxes()
        # Validation of account invoice
        if (dest_company.invoice_auto_validation and
                not float_compare(self.amount_total,
                                  dest_invoice.amount_total,
                                  precision_digits=precision)):
            dest_invoice.signal_workflow('invoice_open')
        else:
            # Add warning in chatter if the total amounts are different
            if float_compare(self.amount_total, dest_invoice.amount_total,
                             precision_digits=precision):
                body = (_(
                    "WARNING!!!!! Failure in the inter-company invoice "
                    "creation process: the total amount of this invoice "
                    "is %s but the total amount in the company %s is %s")
                    % (dest_invoice.amount_total, self.company_id.name,
                       self.amount_total))
                dest_invoice.message_post(body=body)
                dest_invoice.check_total = self.amount_total
        return {'dest_invoice': dest_invoice}

    @api.multi
    def _prepare_invoice_data(self,
                              dest_invoice_lines, dest_inv_type,
                              dest_journal_type, dest_company):
        """ Generate invoice values
            :param dest_invoice_lines : the list of invoice lines to create
            :rtype dest_invoice_line_ids : list of tuples
            :param dest_inv_type : the type of the invoice to prepare "
            "the values
            :param dest_journal_type : type of the journal "
            "to register the invoice_line_ids
            :rtype dest_journal_type : string
            :param dest_company : the company of the created invoice
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        # find the correct journal
        dest_journal = self.env['account.journal'].search([
            ('type', '=', dest_journal_type),
            ('company_id', '=', dest_company.id)
        ], limit=1)
        if not dest_journal:
            raise UserError(_(
                'Please define %s journal for this company: "%s" (id:%d).')
                % (dest_journal_type, dest_company.name, dest_company.id))

        # find periods of supplier company
        context = self._context.copy()
        context['company_id'] = dest_company.id
        dest_period_ids = self.env['account.period'].with_context(
            context).find(self.date_invoice)
        if not dest_period_ids:
            raise UserError(_(
                "Not define period for invoice date '%s' "
                "in this company: '%s' (id:%d).")
                % (self.date_invoice, dest_company.name, dest_company.id))

        # find account, payment term, fiscal position, bank.
        dest_partner_data = self.onchange_partner_id(
            dest_inv_type, self.company_id.partner_id.id,
            company_id=dest_company.id)
        if not self.currency_id.company_id:
            # currency shared between companies
            dest_currency_id = self.currency_id.id
        else:
            # currency not shared between companies
            dest_currency = self.env['res.currency'].search([
                ('name', '=', self.currency_id.name),
                ('company_id', '=', dest_company.id),
            ], limit=1)
            if not dest_currency:
                raise UserError(_(
                    "Could not find the currency '%s' in the company '%s'")
                    % (self.currency_id.name, dest_company.name_get()[0][1]))
            dest_currency_id = dest_currency.id
        return {
            'name': self.name,
            'origin': self.company_id.name + _(' Invoice: ') + str(
                self.number),
            'supplier_invoice_number': self.number,
            'type': dest_inv_type,
            'date_invoice': self.date_invoice,
            'reference': self.reference,
            'account_id': dest_partner_data['value'].get('account_id', False),
            'partner_id': self.company_id.partner_id.id,
            'journal_id': dest_journal.id,
            'invoice_line': dest_invoice_lines,
            'currency_id': dest_currency_id,
            'fiscal_position': dest_partner_data['value'].get(
                'fiscal_position', False),
            'payment_term': dest_partner_data['value'].get(
                'payment_term', False),
            'company_id': dest_company.id,
            'period_id': dest_period_ids and dest_period_ids[0].id or False,
            'partner_bank_id': dest_partner_data['value'].get(
                'partner_bank_id', False),
            'auto_generated': True,
            'auto_invoice_id': self.id,
            'check_total': self.amount_total,
            'comment': self.comment,
        }

    @api.model
    def _prepare_invoice_line_data(self, dest_inv_type, dest_invoice_vals,
                                   dest_company, src_line,
                                   src_company_partner_id):
        """ Generate invoice line values
            :param dest_inv_type : the type of the invoice to prepare "
            "the values
            :param dest_invoice_vals : dict of invoice data
            :rtype dest_invoice_vals : dict
            :param dest_company : the company of the created invoice
            :rtype dest_company : res.company record
            :param src_line : the invoice line object
            :rtype src_line : account.invoice.line record
            :rtype src_company_partner_id : res.partner record
        """
        # get invoice line data from product onchange
        dest_line_data = src_line.product_id_change(
            src_line.product_id.id,
            src_line.product_id.uom_id.id,
            qty=src_line.quantity,
            name='',
            type=dest_inv_type,
            partner_id=src_company_partner_id.id,
            fposition_id=dest_invoice_vals['fiscal_position'],
            company_id=dest_company.id)
        account_id = dest_line_data['value']['account_id']
        account = self.env['account.account'].browse(account_id)
        tax_ids = dest_line_data['value']['invoice_line_tax_id']
        taxes = self.env['account.tax'].browse(tax_ids)
        filtered_account = account.filtered(
            lambda r: r.company_id.id == dest_company.id)
        filtered_taxes = taxes.filtered(
            lambda r: r.company_id.id == dest_company.id)
        dest_line_data['value']['account_id'] = filtered_account.id
        dest_line_data['value']['invoice_line_tax_id'] = [
            (6, 0, filtered_taxes.ids)]
        vals = {
            'name': src_line.name,
            # TODO: it's wrong to just copy the price_unit
            # You have to check if the tax is price_include True or False
            # in source and target companies
            'price_unit': src_line.price_unit,
            'quantity': src_line.quantity,
            'discount': src_line.discount,
            'product_id': src_line.product_id.id or False,
            'uos_id': src_line.uos_id.id or False,
            'sequence': src_line.sequence,
            'invoice_line_tax_id': dest_line_data['value'].get(
                'invoice_line_tax_id', []),
            # Analytic accounts are per company
            # The problem is that we can't really "guess" the
            # analytic account to set. It probably needs to be
            # set via an inherit of this method in a custom module
            'account_analytic_id': dest_line_data['value'].get(
                'account_analytic_id', False),
            'account_id': dest_line_data['value'].get('account_id', False),
            'auto_invoice_line_id': src_line.id
        }
        return vals

    @api.multi
    def action_cancel(self):
        for invoice in self:
            company = self.env['res.company']._find_company_from_partner(
                invoice.partner_id.id)
            if company and not invoice.auto_generated:
                for inter_invoice in self.sudo().search(
                        [('auto_invoice_id', '=', invoice.id)]):
                    inter_invoice.signal_workflow('invoice_cancel')
                    inter_invoice.write({
                        'supplier_invoice_number': False,
                        'origin': invoice.company_id.name +
                        _(' Canceled Invoice: ') + str(invoice.number)})
        return super(AccountInvoice, self).action_cancel()


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    auto_invoice_line_id = fields.Many2one('account.invoice.line',
                                           string='Source Invoice Line',
                                           readonly=True, copy=False,
                                           _prefetch=False)
