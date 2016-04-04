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

    @api.multi
    def _prepare_holding_invoice_line(self):
        self._cr.execute("""SELECT sum(amount_untaxed)
            FROM sale_order
            WHERE id in %s""", (tuple(self.ids),))
        total = self._cr.fetchone()[0]
        return [{
            'name': 'TODO',
            'price_unit': total,
            'quantity': 1,
            }]

    @api.multi
    def _prepare_holding_invoice(self, lines):
        partner_invoice = None
        for sale in self:
            if not partner_invoice:
                partner_invoice = sale.partner_invoice_id
            elif partner_invoice != sale.partner_invoice_id:
                raise UserError(
                    _('Error'),
                    _('Invoice partner must be the same'))
        vals = self.env['sale.order']._prepare_invoice(self[0], lines.ids)
        vals.update({
            'origin': '',  # the list is too long so better to have nothing
            'company_id': self._context.get('force_company'),
            'user_id': self._uid,
            })
        return vals

    @api.model
    def _get_holding_invoice_domain(self, domain, company):
        new_domain = domain[:] if domain is not None else []
        new_domain.extend([
            ('holding_company_id', '=', company.id),
            ('company_id', '!=', company.id),
            ('invoice_state', '=', 'invoiceable'),
        ])
        return new_domain

    @api.multi
    def _scheduler_action_holding_invoice_create(self, domain=None):
        companies = self.env['res.company'].search([])
        invoice_ids = []
        for company in companies:
            new_domain = self._get_holding_invoice_domain(domain, company)
            sales = self.search(new_domain)
            if sales:
                invoice_ids.append(
                    sales.with_context(force_company=company.id)
                         .action_holding_invoice())
        return invoice_ids

    @api.multi
    def _link_holding_invoice_to_order(self, invoice):
        self.write({'holding_invoice_id': invoice.id})

    @api.multi
    def action_holding_invoice(self):
        lines = self.env['account.invoice.line'].browse(False)
        val_lines = self._prepare_holding_invoice_line()
        for val in val_lines:
            lines |= self.env['account.invoice.line'].create(val)
        invoice_vals = self._prepare_holding_invoice(lines)
        invoice = self.env['account.invoice'].create(invoice_vals)
        invoice.button_reset_taxes()
        self._link_holding_invoice_to_order(invoice)
        return invoice.id

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
