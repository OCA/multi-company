# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    auto_generated = fields.Boolean(
        'Auto Generated Document',
        copy=False, default=False)
    auto_invoice_id = fields.Many2one(
        'account.invoice',
        string='Source Invoice',
        readonly=True, copy=False,
        prefetch=False)

    @api.multi
    def _find_company_from_invoice_partner(self):
        self.ensure_one()
        company = self.env['res.company'].sudo().search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)
        return company or False

    @api.multi
    def action_invoice_open(self):
        """ Validated invoice generate cross invoice base on company rules """
        res = super(AccountInvoice, self).action_invoice_open()
        for src_invoice in self:
            # do not consider invoices that have already been auto-generated,
            # nor the invoices that were already validated in the past
            dest_company = src_invoice._find_company_from_invoice_partner()
            if not dest_company or src_invoice.auto_generated:
                return res
            src_invoice.sudo().with_context(force_company=dest_company.id).\
                _inter_company_create_invoice(dest_company)
        return res

    @api.multi
    def _check_intercompany_product(self, dest_company):
        self.ensure_one()
        domain = dest_company._get_user_domain()
        dest_user = self.env['res.users'].search(domain, limit=1)
        if dest_user:
            for line in self.invoice_line_ids:
                try:
                    line.product_id.sudo(dest_user).read(['default_code'])
                except AccessError:
                    raise UserError(_(
                        "You cannot create invoice in company '%s' with "
                        "product '%s' because it is not multicompany")
                        % (dest_company.name, line.product_id.name))

    @api.multi
    def _inter_company_create_invoice(self, dest_company):
        """ create an invoice for the given company : it will copy
                the invoice lines in the new invoice.
            :param dest_company : the company of the created invoice
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        # check intercompany product
        self._check_intercompany_product(dest_company)
        # if an invoice has already been genereted
        # delete it and force the same number
        inter_invoice = self.search([
            ('auto_invoice_id', '=', self.id),
            ('company_id', '=', dest_company.id)
        ])
        force_number = False
        if inter_invoice and inter_invoice.state in ['draft', 'cancel']:
            force_number = inter_invoice.move_name
            inter_invoice.move_name = False
            inter_invoice.unlink()
        # create invoice
        dest_invoice_data = self._prepare_invoice_data(dest_company)
        if force_number:
            dest_invoice_data['move_name'] = force_number
        dest_invoice = self.create(dest_invoice_data)
        # create invoice lines
        for src_line in self.invoice_line_ids:
            if not src_line.product_id:
                raise UserError(_(
                    "The invoice line '%s' doesn't have a product. "
                    "All invoice lines should have a product for "
                    "inter-company invoices.") % src_line.name)
            dest_inv_line_data = src_line._prepare_invoice_line_data(
                dest_invoice, dest_company)
            self.env['account.invoice.line'].create(dest_inv_line_data)
        # add tax_line_ids in created invoice
        dest_invoice_line_ids = dest_invoice.invoice_line_ids
        if (any(
            line.invoice_line_tax_ids for line in dest_invoice_line_ids) and
                not dest_invoice.tax_line_ids):
            dest_invoice.compute_taxes()
        # Validation of account invoice
        precision = self.env['decimal.precision'].precision_get('Account')
        if (dest_company.invoice_auto_validation and
                not float_compare(self.amount_total,
                                  dest_invoice.amount_total,
                                  precision_digits=precision)):
            dest_invoice.action_invoice_open()
        else:
            # Add warning in chatter if the total amounts are different
            if float_compare(self.amount_total, dest_invoice.amount_total,
                             precision_digits=precision):
                body = (_(
                    "WARNING!!!!! Failure in the inter-company invoice "
                    "creation process: the total amount of this invoice "
                    "is %s but the total amount of the invoice %s "
                    "in the company %s is %s")
                    % (dest_invoice.amount_total, self.number,
                       self.company_id.name, self.amount_total))
                dest_invoice.message_post(body=body)
        return {'dest_invoice': dest_invoice}

    @api.multi
    def _get_destination_invoice_type(self):
        self.ensure_one()
        MAP_INVOICE_TYPE = {
            'out_invoice': 'in_invoice',
            'in_invoice': 'out_invoice',
            'out_refund': 'in_refund',
            'in_refund': 'out_refund',
        }
        return MAP_INVOICE_TYPE.get(self.type)

    @api.multi
    def _get_destination_journal_type(self):
        self.ensure_one()
        MAP_JOURNAL_TYPE = {
            'out_invoice': 'purchase',
            'in_invoice': 'sale',
            'out_refund': 'purchase',
            'in_refund': 'sale',
        }
        return MAP_JOURNAL_TYPE.get(self.type)

    @api.multi
    def _prepare_invoice_data(self, dest_company):
        """ Generate invoice values
            :param dest_company : the company of the created invoice
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        dest_inv_type = self._get_destination_invoice_type()
        dest_journal_type = self._get_destination_journal_type()
        # find the correct journal
        dest_journal = self.env['account.journal'].search([
            ('type', '=', dest_journal_type),
            ('company_id', '=', dest_company.id)
        ], limit=1)
        if not dest_journal:
            raise UserError(_(
                'Please define %s journal for this company: "%s" (id:%d).')
                % (dest_journal_type, dest_company.name, dest_company.id))
        # find account, payment term, fiscal position, bank.
        dest_partner_data = {
            'type': dest_inv_type,
            'partner_id': self.company_id.partner_id.id,
            'company_id': dest_company.id,
        }
        dest_partner_data = self.env['account.invoice'].play_onchanges(
            dest_partner_data, ['partner_id'])
        return {
            'name': self.name,
            'origin': _('%s - Invoice: %s') % (self.company_id.name,
                                               self.number),
            'type': dest_inv_type,
            'date_invoice': self.date_invoice,
            'reference': self.reference,
            'account_id': dest_partner_data.get('account_id', False),
            'partner_id': self.company_id.partner_id.id,
            'journal_id': dest_journal.id,
            'currency_id': self.currency_id.id,
            'fiscal_position_id': dest_partner_data.get(
                'fiscal_position_id', False),
            'payment_term_id': dest_partner_data.get(
                'payment_term_id', False),
            'company_id': dest_company.id,
            'partner_bank_id': dest_partner_data.get(
                'partner_bank_id', False),
            'auto_generated': True,
            'auto_invoice_id': self.id,
            'comment': self.comment,
        }

    @api.multi
    def action_invoice_cancel(self):
        for invoice in self:
            company = invoice._find_company_from_invoice_partner()
            if company and not invoice.auto_generated:
                for inter_invoice in self.sudo().search(
                        [('auto_invoice_id', '=', invoice.id)]):
                    inter_invoice.action_invoice_cancel()
                    inter_invoice.write({
                        'origin': _('%s - Canceled Invoice: %s') % (
                            invoice.company_id.name, invoice.number)
                    })
        return super(AccountInvoice, self).action_invoice_cancel()


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    auto_invoice_line_id = fields.Many2one(
        'account.invoice.line',
        string='Source Invoice Line',
        readonly=True, copy=False,
        prefetch=False)

    @api.model
    def _prepare_invoice_line_data(self, dest_invoice, dest_company):
        """ Generate invoice line values
            :param dest_invoice : the created invoice
            :rtype dest_invoice : account.invoice record
            :param dest_company : the company of the created invoice
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        src_company_partner = self.invoice_id.company_id.partner_id
        # get invoice line data from product onchange
        dest_line_data = {
            'product_id': self.product_id.id,
            'uom_id': self.product_id.uom_id.id,
            'quantity': self.quantity,
            'name': '',
            'partner_id': src_company_partner.id,
            'company_id': dest_company.id,
            'invoice_id': dest_invoice.id,
        }
        dest_line_data = self.env['account.invoice.line'].play_onchanges(
            dest_line_data, ['product_id'])
        account_id = dest_line_data.get('account_id', False)
        if account_id:
            account = self.env['account.account'].browse(account_id)
        else:
            account = self.env['account.account'].search([
                ('user_type_id', '=', self.env.ref(
                    'account.data_account_type_revenue').id),
                ('company_id', '=', dest_company.id)], limit=1)
            if not account:
                raise UserError(_(
                    'Please define %s account for this company: "%s" (id:%d).')
                    % (self.env.ref('account.data_account_type_revenue').name,
                       dest_company.name, dest_company.id))
        tax_ids = dest_line_data.get('invoice_line_tax_ids', False)
        vals = {
            'name': self.name,
            # TODO: it's wrong to just copy the price_unit
            # You have to check if the tax is price_include True or False
            # in source and target companies
            'price_unit': self.price_unit,
            'quantity': self.quantity,
            'discount': self.discount,
            'product_id': self.product_id.id or False,
            'sequence': self.sequence,
            'invoice_line_tax_ids': tax_ids or [],
            # Analytic accounts are per company
            # The problem is that we can't really "guess" the
            # analytic account to set. It probably needs to be
            # set via an inherit of this method in a custom module
            'account_analytic_id': dest_line_data.get(
                'account_analytic_id', False),
            'account_id': account.id or False,
            'auto_invoice_line_id': self.id,
            'invoice_id':  dest_line_data.get('invoice_id', False),
            'partner_id': src_company_partner.id,
            'company_id': dest_company.id,
        }
        return vals
