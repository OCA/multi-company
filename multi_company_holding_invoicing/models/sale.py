# -*- coding: utf-8 -*-
# © 2015 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    holding_company_id = fields.Many2one(
        'res.company',
        related='section_id.holding_company_id',
        string='Holding Company for Invoicing',
        readonly=True,
        copy=False,
        store=True)

    holding_invoice_id = fields.Many2one(
        'account.invoice',
        string='Holding Invoice',
        copy=False,
        readonly=True)

    invoice_state = fields.Selection([
        ('none', 'Not Applicable'),
        ('not_ready', 'Not Ready'),
        ('invoiceable', 'Invoiceable'),
        ('pending', 'Pending'),
        ('invoiced', 'Invoiced'),
        ], string='Holding Invoice Control',
        copy=False,
        compute='_compute_invoice_state',
        store=True)

    @api.one
    @api.depends('shipped', 'section_id.holding_company_id')
    def _compute_invoice_state(self):
        # Note for perf issue the 'holding_invoice_id.state' is not set here
        # as a dependency. Indeed the dependency is manually triggered when
        # the holding_invoice is generated or the state is changed
        for sale in self:
            if not sale.section_id.holding_company_id\
                    or sale.section_id.holding_company_id == sale.company_id:
                sale.invoice_state = 'none'
            elif sale.holding_invoice_id:
                if sale.holding_invoice_id.state in ('open', 'done'):
                    sale.invoice_state = 'invoiced'
                else:
                    sale.invoice_state = 'pending'
            elif sale.shipped:
                sale.invoice_state = 'invoiceable'
            else:
                sale.invoice_state = 'not_ready'

    @api.multi
    def _set_invoice_state(self, state):
        if self:
            self._cr.execute("""UPDATE sale_order
                SET invoice_state=%s
                WHERE id in %s""", (state, tuple(self.ids)))
            self.invalidate_cache()

    @api.onchange('section_id')
    def onchange_section_id(self):
        if self.section_id and self.section_id.holding_company_id:
            self.order_policy = 'manual'

    @api.model
    def _prepare_holding_invoice_line(self, data):
        return [{
            'name': _('Global Invoice'),
            'price_unit': data['amount_total'],
            'quantity': 1,
            }]

    @api.model
    def _prepare_holding_invoice(self, data, lines):
        # get default from native method _prepare_invoice
        # use first sale order as partner and section are the same
        sale = self.search(data['__domain'], limit=1)
        vals = self.env['sale.order']._prepare_invoice(sale, lines.ids)
        vals.update({
            'origin': _('Holding Invoice'),
            'company_id': self._context['force_company'],
            'user_id': self._uid,
            })
        return vals

    @api.multi
    def _link_holding_invoice_to_order(self, invoice):
        self._cr.execute("""UPDATE sale_order
            SET holding_invoice_id=%s, invoice_state='pending'
            WHERE id in %s""", (invoice.id, tuple(self.ids)))
        self.invalidate_cache()

    @api.model
    def _get_holding_group_fields(self):
        return [
            ['partner_invoice_id', 'section_id', 'amount_total'],
            ['partner_invoice_id', 'section_id'],
        ]

    @api.model
    def _get_holding_invoice_data(self, domain):
        read_fields, groupby = self._get_holding_group_fields()
        return self.read_group(domain, read_fields, groupby, lazy=False)

    @api.model
    def _generate_holding_invoice(self, domain):
        invoices = self.env['account.invoice'].browse(False)
        _logger.debug('Retrieve data for generating the holding invoice')
        for data in self._get_holding_invoice_data(domain):
            section = self.env['crm.case.section'].browse(
                data['section_id'][0])
            company = section.holding_company_id
            env = self.with_context(force_company=company.id).env
            inv_obj = env['account.invoice']
            inv_line_obj = env['account.invoice.line']
            sale_obj = env['sale.order']
            _logger.debug('Prepare vals for holding invoice')
            lines = inv_line_obj.browse(False)
            val_lines = sale_obj._prepare_holding_invoice_line(data)
            for val in val_lines:
                lines |= inv_line_obj.create(val)
            invoice_vals = sale_obj._prepare_holding_invoice(data, lines)
            _logger.debug('Generate the holding invoice')
            invoice = inv_obj.create(invoice_vals)
            invoice.button_reset_taxes()
            sales = sale_obj.search(data['__domain'])
            _logger.debug('Link the holding invoice with the sale order')
            sales._link_holding_invoice_to_order(invoice)
            invoices |= invoice
        return invoices

    @api.multi
    def action_holding_invoice(self):
        return self._generate_holding_invoice([('id', 'in', self.ids)])

    @api.multi
    def write(self, values):
        section_id = values.get('section_id', False)
        if section_id:
            section = self.env['crm.case.section'].browse(section_id)
            if section.holding_company_id:
                values.update({'order_policy': 'manual'})
        return super(SaleOrder, self).write(values)

    @api.model
    def create(self, values):
        section_id = values.get('section_id', False)
        if section_id:
            section = self.env['crm.case.section'].browse(section_id)
            if section.holding_company_id:
                values.update({'order_policy': 'manual'})
        return super(SaleOrder, self).create(values)

    @api.model
    def _prepare_child_invoice_line(self, data):
        section = self.env['crm.case.section'].browse(data['section_id'][0])
        domain = []
        for arg in data['__domain']:
            if len(arg) == 3:
                domain.append(('order_id.%s' % arg[0], arg[1], arg[2]))
        line_ids = self.env['sale.order.line'].search(domain).ids
        return [{
            'name': _('Global Invoice'),
            'price_unit': data['amount_total'],
            'quantity': 1,
            'sale_line_ids': [(6, 0, line_ids)],
            }, {
            'name': _('Royalty'),
            'price_unit': data['amount_total'],
            'quantity': - section.holding_discount/100.,
            'sale_line_ids': [],
            }]

    @api.model
    def _prepare_child_invoice(self, data, lines):
        # get default from native method _prepare_invoice
        # use first sale order as partner and section are the same
        sale = self.search(data['__domain'], limit=1)
        vals = self.env['sale.order']._prepare_invoice(sale, lines.ids)
        vals.update({
            'origin': sale.holding_invoice_id.name,
            'company_id': sale.company_id.id,
            'user_id': self._uid,
            })
        return vals

    @api.model
    def _get_child_group_fields(self):
        return [
            ['partner_invoice_id', 'section_id', 'company_id', 'amount_total'],
            ['partner_invoice_id', 'section_id', 'company_id'],
        ]

    @api.model
    def _get_child_invoice_data(self, domain):
        read_fields, groupby = self._get_child_group_fields()
        return self.read_group(domain, read_fields, groupby, lazy=False)

    @api.model
    def _generate_child_invoice(self, domain):
        invoices = self.env['account.invoice'].browse(False)
        for data in self._get_child_invoice_data(domain):
            env = self.with_context(force_company=data['company_id'][0]).env
            inv_obj = env['account.invoice']
            inv_line_obj = env['account.invoice.line']
            sale_obj = env['sale.order']
            sale_line_obj = env['sale.order.line']
            lines = inv_line_obj.browse(False)
            val_lines = sale_obj._prepare_child_invoice_line(data)
            for val in val_lines:
                lines |= inv_line_obj.create(val)
            invoice_vals = sale_obj._prepare_child_invoice(data, lines)
            invoice = inv_obj.create(invoice_vals)
            invoice.button_reset_taxes()
            sales = sale_obj.search(data['__domain'])
            sales.write({'invoice_ids': [(6, 0, [invoice.id])]})
            order_lines = sale_line_obj.browse(False)
            for sale in self:
                for line in sale.order_line:
                    order_lines |= line
            order_lines._store_set_values(['invoiced'])
            # Dummy call to workflow, will not create another invoice
            # but bind the new invoice to the subflow
            sales.signal_workflow('manual_invoice')
            invoices |= invoice
        return invoices

    @api.multi
    def action_child_invoice(self):
        return self._generate_child_invoice([('id', 'in', self.ids)])

    @api.model
    def _make_invoice(self, order, lines):
        if order.section_id.holding_company_id:
            raise UserError('The sale order %s must be invoiced via '
                            'the holding company')
        else:
            return super(SaleOrder, self)._make_invoice(order, lines)
