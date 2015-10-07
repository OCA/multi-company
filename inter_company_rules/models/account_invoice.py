# -*- coding: utf-8 -*-
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning
from openerp import SUPERUSER_ID


class account_invoice(orm.Model):

    _inherit = 'account.invoice'

    _columns = {
        'auto_generated': fields.boolean(string='Auto Generated Document'),
        'auto_invoice_id': fields.many2one('account.invoice',
                                           string='Source Invoice',
                                           readonly=True)}

    def copy_data(self, cr, uid, _id, default=None, context=None):
        vals = super(account_invoice, self).copy_data(cr, uid, _id,
                                                      default, context)
        vals.update({'auto_generated': False,
                     'auto_invoice_id': False})
        return vals

    def invoice_validate(self, cr, uid, ids, context=None):
        """ Validated invoice generate cross invoice base on company rules """
        for invoice in self.browse(cr, uid, ids, context=context):
            # do not consider invoices that have already been auto-generated,
            # nor the invoices that were already validated in the past
            company = self.pool['res.company']._find_company_from_partner(
                cr, uid, invoice.partner_id.id, context=context)
            if (company and company.auto_generate_invoices and
                    not invoice.auto_generated):
                if invoice.type == 'out_invoice':
                    self.inter_company_create_invoice(
                        cr, uid, invoice, company, 'in_invoice', 'purchase',
                        context=context)
                elif invoice.type == 'in_invoice':
                    self.inter_company_create_invoice(
                        cr, uid, invoice, company, 'out_invoice', 'sale',
                        context=context)
                elif invoice.type == 'out_refund':
                    self.inter_company_create_invoice(
                        cr, uid, invoice, company, 'in_refund',
                        'purchase_refund', context=context)
                elif invoice.type == 'in_refund':
                    self.inter_company_create_invoice(
                        cr, uid, invoice, company, 'out_refund', 'sale_refund',
                        context=context)
        return super(account_invoice, self).invoice_validate(cr, uid, ids,
                                                             context=context)

    def inter_company_create_invoice(self, cr, uid, invoice, company, inv_type,
                                     journal_type, context=None):
        """ create an invoice for the given company : it wil copy "
        "the invoice lines in the new
            invoice. The intercompany user is the author of the new invoice.
            :param invoice : the invoice
            :rtype invoice : account.invoice record
            :param company : the company of the created invoice
            :rtype company : res.company record
            :param inv_type : the type of the invoice "
            "('in_refund', 'out_refund', 'in_invoice', ...)
            :rtype inv_type : string
            :param journal_type : the type of the journal "
            "to register the invoice
            :rtype journal_type : string
        """
        # find user for creating the invoice from company
        intercompany_uid = (company.intercompany_user_id and
                            company.intercompany_user_id.id or False)
        if not intercompany_uid:
            raise Warning(_(
                'Provide one user for intercompany relation for % ')
                % company.name)

        if context is None:
            context = {}
        ctx = context.copy()
        ctx['force_company'] = company.id
        origin_partner_id = invoice.company_id.partner_id
        invoice_line_ids = []
        invoice_line_obj = self.pool['account.invoice.line']
        for line in invoice.invoice_line:
            # get invoice line data from product onchange
            product_uom_id = (line.product_id.uom_id and
                              line.product_id.uom_id.id or False)
            line_data = invoice_line_obj.product_id_change(
                cr, SUPERUSER_ID,
                line.id,
                line.product_id.id,
                product_uom_id,
                qty=line.quantity,
                name='',
                type=inv_type,
                partner_id=origin_partner_id.id,
                fposition_id=origin_partner_id.property_account_position.id,
                company_id=company.id, context=ctx)

            # create invoice line, as the intercompany user
            inv_line_data = self._prepare_invoice_line_data(
                cr, SUPERUSER_ID, line_data, line, context=ctx)
            inv_line_id = invoice_line_obj.create(cr, intercompany_uid,
                                                  inv_line_data, context=ctx)
            invoice_line_ids.append(inv_line_id)
        # create invoice, as the intercompany user
        invoice_vals = self._prepare_invoice_data(
            cr, SUPERUSER_ID, invoice, invoice_line_ids, inv_type,
            journal_type, company, context=ctx)
        return self.create(cr, intercompany_uid, invoice_vals,
                           context=ctx)

    def _prepare_invoice_data(self, cr, uid, invoice,
                              invoice_line_ids, inv_type,
                              journal_type, company, context=None):
        """ Generate invoice values
            :param invoice : the invoice
            :rtype invoice : account.invoice record
            :param invoice_line_ids : the ids of the invoice lines
            :rtype invoice_line_ids : array of integer
            :param inv_type : the type of the invoice to prepare the values
            :param journal_type : type of the journal "
            "to register the invoice_line_ids
            :rtype journal_type : string
            :rtype company : res.company record
        """
        # find the correct journal
        journal_id = self.pool['account.journal'].search(
            cr, uid, [('type', '=', journal_type),
                      ('company_id', '=', company.id)],
            limit=1, context=context)
        if not journal_id:
            raise Warning(_(
                'Please define %s journal for this company: "%s" (id:%d).')
                % (journal_type, company.name, company.id))

        # find periods of supplier company
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['company_id'] = company.id
        period_ids = self.pool['account.period'].find(
            cr, uid, invoice.date_invoice, context=ctx)

        # find account, payment term, fiscal position, bank.
        partner_data = self.onchange_partner_id(
            cr, uid, invoice.id, inv_type,
            invoice.company_id.partner_id.id,
            company_id=company.id)

        return {
            'name': invoice.name,
            # TODO : not sure !!
            'origin': invoice.company_id.name + _(' Invoice: ') + str(
                invoice.number),
            'type': inv_type,
            'date_invoice': invoice.date_invoice,
            'reference': invoice.reference,
            'account_id': partner_data['value'].get('account_id', False),
            'partner_id': invoice.company_id.partner_id.id,
            'journal_id': journal_id[0],
            'invoice_line': [(6, 0, invoice_line_ids)],
            'currency_id': invoice.currency_id and invoice.currency_id.id,
            'fiscal_position': partner_data['value'].get(
                'fiscal_position', False),
            'payment_term': partner_data['value'].get('payment_term', False),
            'company_id': company.id,
            'period_id': period_ids and period_ids[0] or False,
            'partner_bank_id': partner_data['value'].get(
                'partner_bank_id', False),
            'auto_generated': True,
            'auto_invoice_id': invoice.id,
        }

    def _prepare_invoice_line_data(self, cr, uid, line_data, line,
                                   context=None):
        """ Generate invoice line values
            :param line_data : dict of invoice line data
            :rtype line_data : dict
            :param line : the invoice line object
            :rtype line : account.invoice.line record
        """
        vals = {
            'name': line.name,
            'price_unit': line.price_unit,
            'quantity': line.quantity,
            'discount': line.discount,
            'product_id': line.product_id.id or False,
            'uos_id': line.uos_id.id or False,
            'sequence': line.sequence,
            'invoice_line_tax_id': [(6, 0, line_data['value'].get(
                'invoice_line_tax_id', []))],
            'account_analytic_id': line.account_analytic_id.id or False,
        }
        if line_data['value'].get('account_id'):
            vals['account_id'] = line_data['value']['account_id']
        return vals
