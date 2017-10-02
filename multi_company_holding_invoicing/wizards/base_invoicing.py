# -*- coding: utf-8 -*-
# © 2015 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, api, _
import logging
_logger = logging.getLogger(__name__)


class BaseHoldingInvoicing(models.AbstractModel):
    _name = 'base.holding.invoicing'

    @api.model
    def _get_invoice_line_data(self, data):
        if self._context.get('section_group_by') == 'none':
            return [data]
        else:
            read_fields, groupby = self._get_group_fields()
            read_fields += ['name', 'client_order_ref']
            groupby += ['name', 'client_order_ref']
            return self.env['sale.order'].read_group(
                data['__domain'], read_fields, groupby, lazy=False)

    @api.model
    def _get_accounting_value_from_product(self, data_line, product):
        # We do not have access to the partner here so we can not
        # play correctly the onchange
        # We need to refactor the way to generate the line
        # Refactor will be done in V10
        # for now we just read the info on the product
        # you need to set the tax by yourself
        if self._context.get('section_group_by') == 'none':
            name = product.name
        else:
            name = '%s - %s' % (
                data_line['name'], data_line.get('client_order_ref', ''))
        return {
            'name': name,
            'product_id': product.id,
            'account_id': product.property_account_income.id,
        }

    @api.model
    def _prepare_invoice_line(self, data_line):
        section = self.env['crm.case.section'].browse(
            data_line['section_id'][0])
        vals = self._get_accounting_value_from_product(
            data_line, section.holding_product_id)
        vals.update({
            'price_unit': data_line['amount_untaxed'],
            'quantity': data_line.get('quantity', 1),
        })
        return vals

    @api.model
    def _prepare_invoice(self, data, lines):
        # get default from native method _prepare_invoice
        # use first sale order as partner and section are the same
        sale = self.env['sale.order'].search(data['__domain'], limit=1)
        vals = self.env['sale.order']._prepare_invoice(sale, lines.ids)
        vals.update({
            'origin': _('Holding Invoice'),
            'company_id': self._context['force_company'],
            'user_id': self._uid,
            })
        return vals

    @api.model
    def _get_group_fields(self):
        return NotImplemented

    @api.model
    def _get_invoice_data(self, domain):
        read_fields, groupby = self._get_group_fields()
        return self.env['sale.order'].read_group(
            domain, read_fields, groupby, lazy=False)

    @api.model
    def _get_company_invoice(self, data):
        return NotImplemented

    @api.model
    def _link_sale_order(self, invoice, sales):
        return NotImplemented

    @api.model
    def _create_inv_lines(self, val_lines):
        inv_line_obj = self.env['account.invoice.line']
        lines = inv_line_obj.browse(False)
        for val_line in val_lines:
            lines |= inv_line_obj.create(val_line)
        return lines

    @api.model
    def _generate_invoice(self, domain, date_invoice=None):
        self = self.suspend_security()
        invoices = self.env['account.invoice'].browse(False)
        _logger.debug('Retrieve data for generating the invoice')
        for data in self._get_invoice_data(domain):
            company = self._get_company_invoice(data)

            section = self.env['crm.case.section'].browse(
                data['section_id'][0])

            # add company and section info in the context
            loc_self = self.with_context(
                force_company=company.id,
                invoice_date=date_invoice,
                section_id=section.id,
                section_group_by=section.holding_invoice_group_by)

            _logger.debug('Prepare vals for holding invoice')
            data_lines = loc_self._get_invoice_line_data(data)
            val_lines = []
            for data_line in data_lines:
                val_lines.append(loc_self._prepare_invoice_line(data_line))
            lines = loc_self._create_inv_lines(val_lines)
            invoice_vals = loc_self._prepare_invoice(data, lines)
            _logger.debug('Generate the holding invoice')
            invoice = loc_self.env['account.invoice'].create(invoice_vals)
            invoice.button_reset_taxes()
            _logger.debug('Link the invoice with the sale order')
            sales = self.env['sale.order'].search(data['__domain'])
            self._link_sale_order(invoice, sales)
            invoices |= invoice
        return invoices


class HoldingInvoicing(models.TransientModel):
    _inherit = 'base.holding.invoicing'
    _name = 'holding.invoicing'

    @api.model
    def _get_group_fields(self):
        return [
            ['partner_invoice_id', 'section_id', 'amount_untaxed'],
            ['partner_invoice_id', 'section_id'],
        ]

    @api.model
    def _get_company_invoice(self, data):
        section = self.env['crm.case.section'].browse(
            data['section_id'][0])
        return section.holding_company_id

    @api.model
    def _link_sale_order(self, invoice, sales):
        self._cr.execute("""UPDATE sale_order
            SET holding_invoice_id=%s, invoice_state='pending'
            WHERE id in %s""", (invoice.id, tuple(sales.ids)))
        invoice.invalidate_cache()


class ChildInvoicing(models.TransientModel):
    _inherit = 'base.holding.invoicing'
    _name = 'child.invoicing'

    @api.model
    def _get_company_invoice(self, data):
        return self.env['res.company'].browse(data['company_id'][0])

    @api.model
    def _link_sale_order(self, invoice, sales):
        sales.write({'invoice_ids': [(6, 0, [invoice.id])]})
        order_lines = self.env['sale.order.line'].search([
            ('order_id', 'in', sales.ids),
            ])
        order_lines._store_set_values(['invoiced'])
        # Dummy call to workflow, will not create another invoice
        # but bind the new invoice to the subflow
        sales.signal_workflow('manual_invoice')

    @api.model
    def _get_invoice_line_data(self, data):
        section = self.env['crm.case.section'].browse(
            data['section_id'][0])
        data_lines = super(ChildInvoicing, self)._get_invoice_line_data(data)
        data_lines.append({
            'name': 'royalty',
            'amount_untaxed': data['amount_untaxed'],
            'quantity': - section.holding_discount/100.,
            'sale_line_ids': [],
            'section_id': [section.id],
            })
        return data_lines

    @api.model
    def _prepare_invoice_line(self, data_line):
        val_line = super(ChildInvoicing, self).\
            _prepare_invoice_line(data_line)
        if data_line.get('__domain'):
            order_ids = self.env['sale.order'].search(
                data_line['__domain']).ids
            line_ids = self.env['sale.order.line'].search([
                ('order_id', 'in', order_ids)]).ids
            val_line['sale_line_ids'] = [(6, 0, line_ids)]
        # TODO the code is too complicated
        # we should simplify the _get_invoice_line_data
        # and _prepare_invoice_line to avoid this kind of hack
        if data_line.get('name') == 'royalty':
            section = self.env['crm.case.section'].browse(
                data_line['section_id'][0])
            val_line.update(self._get_accounting_value_from_product(
                data_line,
                section.holding_royalty_product_id))
            val_line['name'] = section.holding_royalty_product_id.name
        return val_line

    @api.model
    def _prepare_invoice(self, data, lines):
        vals = super(ChildInvoicing, self)._prepare_invoice(data, lines)
        sale = self.env['sale.order'].search(data['__domain'], limit=1)
        holding_invoice = sale.holding_invoice_id
        vals['origin'] = holding_invoice.name
        vals['partner_id'] = holding_invoice.company_id.partner_id.id
        section = self.env['crm.case.section'].browse(data['section_id'][0])
        vals['journal_id'] = section.journal_id.id
        partner_data = self.env['account.invoice'].onchange_partner_id(
            'out_invoice', holding_invoice.company_id.partner_id.id,
            company_id=self._context['force_company'])
        vals['account_id'] = partner_data['value'].get('account_id', False)
        return vals

    @api.model
    def _get_group_fields(self):
        return [
            ['partner_invoice_id', 'section_id',
             'company_id', 'amount_untaxed'],
            ['partner_invoice_id', 'section_id', 'company_id'],
        ]
