# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - Pedro M. Baeza

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import config, float_compare
from odoo.tests.common import Form


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
            ('partner_id', '=', self.commercial_partner_id.id)
        ], limit=1)
        return company or False

    @api.multi
    def action_invoice_open(self):
        """ Validated invoice generate cross invoice base on company rules """
        res = super(AccountInvoice, self).action_invoice_open()
        # Don't generate inter-company invoices when testing unrelated modules
        if (config["test_enable"] and not
                self.env.context.get("test_account_invoice_inter_company")):
            return
        for src_invoice in self:
            # do not consider invoices that have already been auto-generated,
            # nor the invoices that were already validated in the past
            dest_company = src_invoice._find_company_from_invoice_partner()
            if not dest_company or src_invoice.auto_generated:
                continue
            src_invoice.sudo().with_context(force_company=dest_company.id).\
                _inter_company_create_invoice(dest_company)
        return res

    @api.multi
    def _check_intercompany_product(self, dest_company):
        self.ensure_one()
        if dest_company.company_share_product:
            return
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
        # if an invoice has already been generated
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
        dest_inv_line_data = []
        for src_line in self.invoice_line_ids:
            if not src_line.product_id:
                raise UserError(_(
                    "The invoice line '%s' doesn't have a product. "
                    "All invoice lines should have a product for "
                    "inter-company invoices.") % src_line.name)
            dest_inv_line_data.append(src_line._prepare_invoice_line_data(
                dest_invoice, dest_company))
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
        # Use test.Form() class to trigger propper onchanges on the invoice
        dest_invoice_data = Form(
            self.env['account.invoice'].with_context(
                default_type=dest_inv_type,
                force_company=dest_company.id
            ))
        dest_invoice_data.company_id = dest_company
        dest_invoice_data.partner_id = self.company_id.partner_id
        dest_invoice_data.name = self.name
        dest_invoice_data.date_invoice = self.date_invoice
        dest_invoice_data.reference = self.number
        dest_invoice_data.comment = self.comment
        dest_invoice_data.journal_id = dest_journal
        dest_invoice_data.currency_id = self.currency_id
        vals = dest_invoice_data._values_to_save(all_fields=True)
        vals.update({
            'origin': _('%s - Invoice: %s') % (
                self.company_id.name, self.number),
            'auto_invoice_id': self.id,
            'comment': self.comment,
            'auto_generated': True,
        })
        return vals

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
        # Use test.Form() class to trigger propper onchanges on the line
        product = self.product_id or False
        dest_invoice_form = Form(
            dest_invoice.with_context(force_company=dest_company.id),
            'account_invoice_inter_company.invoice_supplier_form',
        )
        with dest_invoice_form.invoice_line_ids.new() as invoice_line:
            # HACK: Related fields manually set due to Form() limitations
            invoice_line.company_id = dest_invoice.company_id
            invoice_line.currency_id = dest_invoice.currency_id
            invoice_line.partner_id = dest_invoice.partner_id
            invoice_line.invoice_type = dest_invoice.type
            invoice_line.company_currency_id = dest_invoice.company_currency_id
            # Regular fields
            invoice_line.product_id = product
            invoice_line.name = self.name
            invoice_line.uom_id = self.product_id.uom_id
            invoice_line.quantity = self.quantity
            # TODO: it's wrong to just copy the price_unit
            # You have to check if the tax is price_include True or False
            # in source and target companies
            invoice_line.price_unit = self.price_unit
            invoice_line.discount = self.discount
            invoice_line.sequence = self.sequence
        vals = dest_invoice_form._values_to_save(
            all_fields=True)['invoice_line_ids'][0][2]
        vals.update({
            'auto_invoice_line_id': self.id,
            'invoice_id': dest_invoice.id,
        })
        if (self.account_analytic_id and
                not self.account_analytic_id.company_id):
            vals["account_analytic_id"] = self.account_analytic_id.id
            analytic_tags = self.analytic_tag_ids.filtered(
                lambda x: not x.company_id)
            if analytic_tags:
                vals["analytic_tag_ids"] = [(4, x) for x in analytic_tags.ids]
        return vals
