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

    # TODO rethink
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
        compute='_get_invoice_state',
        store=True)

    @api.one
    @api.depends('shipped', 'holding_invoice_id',
                 'section_id.holding_company_id')
    def _get_invoice_state(self):
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

    @api.onchange('section_id')
    def onchange_section_id(self):
        if self.section_id and self.section_id.holding_company_id:
            self.order_policy = 'manual'

    @api.model
    def _prepare_holding_invoice_line(self, data):
        return [{
            'name': 'Global Invoice',
            'price_unit': data['amount_total'],
            'quantity': 1,
            }]

    @api.model
    def _prepare_holding_invoice(self, data, lines):
        # get default from native method _prepare_invoice
        # use first sale order as partner and section are the same
        sale = self.search(data['__domain'], limit=1)
        vals = self.env['sale.order']._prepare_invoice(sale, lines.ids)
        section = self.env['crm.case.section'].browse(data['section_id'][0])
        vals.update({
            'origin': u'holding grouped',
            'company_id': section.holding_company_id.id,
            'user_id': self._uid,
            })
        return vals

    @api.multi
    def _link_holding_invoice_to_order(self, invoice):
        self.write({'holding_invoice_id': invoice.id})

    @api.model
    def _get_holding_group_fields(self):
        return [
            ['partner_id', 'section_id', 'amount_total'],
            ['partner_id', 'section_id'],
        ]

    @api.model
    def _get_holding_invoice_data(self, domain):
        read_fields, groupby = self._get_holding_group_fields()
        return self.read_group(domain, read_fields, groupby, lazy=False)

    @api.model
    def _generate_holding_invoice(self, domain):
        for data in self._get_holding_invoice_data(domain):
            lines = self.env['account.invoice.line'].browse(False)
            val_lines = self._prepare_holding_invoice_line(data)
            for val in val_lines:
                lines |= self.env['account.invoice.line'].create(val)
            invoice_vals = sales._prepare_holding_invoice(data, lines)
            invoice = self.env['account.invoice'].create(invoice_vals)
            invoice.button_reset_taxes()
            sales = self.search(data['__domain'])
            sales._link_holding_invoice_to_order(invoice)
        return invoice.id

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

    @api.multi
    def _prepare_child_invoice_line(self):
        total = 0
        sale_lines = self.env['sale.order.line'].browse(False)
        for sale in self:
            total += sale.amount_untaxed
            sale_lines |= sale.order_line
        return [{
            'name': self[0].holding_invoice_id.invoice_line[0].name,
            'price_unit': total,
            'quantity': 1,
            'sale_line_ids': [(6, 0, sale_lines.ids)],
            }, {
            'name': 'Redevance',
            'price_unit': total,
            'quantity': - self[0].section_id.holding_discount/100.,
            'sale_line_ids': [],
            }]

    @api.multi
    def _prepare_child_invoice(self, lines):
        vals = self.env['sale.order']._prepare_invoice(self[0], lines)
        holding_invoice = self[0].holding_invoice_id
        journal = self.env['account.journal'].search([
            ('company_id', '=', self._context['force_company']),
            ('type', '=', 'sale'),
            ])
        vals.update({
            'journal_id': journal.id,
            'origin': holding_invoice.number,
            'company_id': self._context['force_company'],
            'user_id': self._uid,
            'partner_id': holding_invoice.company_id.partner_id.id,
            'holding_invoice_id': holding_invoice.id,
            })
        return vals

    @api.multi
    def action_child_invoice(self):
        lines = self.env['account.invoice.line'].browse(False)
        val_lines = self._prepare_child_invoice_line()
        for val in val_lines:
            lines |= self.env['account.invoice.line'].create(val)
        invoice_vals = self._prepare_child_invoice(lines.ids)
        invoice = self.env['account.invoice'].create(invoice_vals)
        self.write({'invoice_ids': [(6, 0, [invoice.id])]})
        invoice.button_reset_taxes()
        order_lines = self.env['sale.order.line'].browse(False)
        for sale in self:
            for line in sale.order_line:
                order_lines |= line
        order_lines._store_set_values(['invoiced'])
        return invoice

    @api.model
    def _make_invoice(self, order, lines):
        if order.section_id.holding_company_id:
            raise UserError('The sale order %s must be invoiced via '
                            'the holding company')
        else:
            return super(SaleOrder, self)._make_invoice(order, lines)
