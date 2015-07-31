# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 AKRETION (<http://www.akretion.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api, _
from openerp.exceptions import Warning
from openerp.addons.stock_account.wizard.stock_invoice_onshipping import (
    stock_invoice_onshipping)

ori_view_init = stock_invoice_onshipping.view_init


def view_init(self, fields_list):
    if self.env['stock.picking']._columns.get('holding_invoice_id'):
        active_ids = self._context.get('active_ids', [])
        user = self.env['res.users'].browse(self._context['uid'])
        company_id = user.company_id.id
        for picking in self.env['stock.picking'].browse(active_ids):
            if (
                (company_id == picking.holding_company_id.id and
                 picking.sale_id.section_id.holding_customer_automatic_invoice)
                or
                (company_id == picking.company_id.id and
                 picking.sale_id.section_id.holding_supplier_automatic_invoice)
            ):
                raise Warning(_(
                    "You are not allowed to create invoices manually"
                    " from the selected pickings because they are created "
                    "automatically"))
            elif picking.invoice_id:
                raise Warning(_(
                    'An invoice already exists for the picking %s')
                    % (picking.name or ''))
        return super(stock_invoice_onshipping, self).view_init(fields_list)
    return ori_view_init(self, fields_list)

stock_invoice_onshipping.view_init = view_init


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    @api.depends('move_lines', 'move_lines.holding_invoice_state')
    def get_holding_invoice_state(self):
        holding_invoice_state = 'none'
        for move in self.move_lines:
            if move.holding_invoice_state == 'invoiced':
                holding_invoice_state = 'invoiced'
            elif move.holding_invoice_state == '2binvoiced':
                holding_invoice_state = '2binvoiced'
                break
        self.holding_invoice_state = holding_invoice_state

    section_id = fields.Many2one('crm.case.section', string='Sales Team',
                                 related='group_id.section_id',
                                 readonly=True)
    holding_invoice_id = fields.Many2one('account.invoice',
                                         string='Holding Invoice',
                                         readonly=True)
    holding_invoice_state = fields.Selection([
        ('invoiced', 'Invoiced'),
        ('2binvoiced', 'To Be Invoiced'),
        ('none', 'Not Applicable')
    ], string='Holding Invoice Control',
        compute='get_holding_invoice_state', store=True)
    holding_company_id = fields.Many2one(
        'res.company',
        related='group_id.holding_company_id',
        string='Holding Company for Invoicing', readonly=True)
    holding_customer_automatic_invoice = fields.Boolean(
        related='group_id.holding_customer_automatic_invoice',
        string='Automatic invoice for holding customer', readonly=True)
    holding_supplier_automatic_invoice = fields.Boolean(
        related='group_id.holding_supplier_automatic_invoice',
        string='Automatic invoice for holding supplier', readonly=True)

    @api.model
    def check_move_to_invoice(self, move, key, todo):
        holding_invoice = self._context.get('holding_invoice', False)
        if holding_invoice:
            if move.holding_invoice_state == '2binvoiced':
                if (move.state != 'cancel') and not move.scrapped:
                    todo.setdefault(key, [])
                    todo[key].append(move)
            return
        else:
            return super(StockPicking, self).check_move_to_invoice(
                move, key, todo)

    @api.model
    def _get_partner_to_invoice(self, picking):
        holding_invoice = self._context.get('holding_invoice', False)
        if picking.holding_company_id and not holding_invoice:
            return (picking.holding_company_id.partner_id and
                    picking.holding_company_id.partner_id.id)
        else:
            return (picking.sale_id.partner_invoice_id and
                    picking.sale_id.partner_invoice_id.id)

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        invoice_vals = super(StockPicking, self)._get_invoice_vals(
            key, inv_type, journal_id, move)
        invoice_vals['company_id'] = self._context['force_company']
        invoice_vals['user_id'] = self._uid
        journal_ids = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self._context['force_company'])
        ])
        invoice_vals['journal_id'] = journal_ids[0].id
        account = self.env['account.account'].browse(
            invoice_vals['account_id'])
        if account.company_id.id != invoice_vals['company_id']:
            invoice_vals['account_id'] = (move.partner_id.
                                          property_account_receivable.id)
        return invoice_vals

    @api.model
    def _get_invoice_domain(self, domain, company):
        new_domain = domain[:] if domain is not None else []
        new_domain.extend([
            ('group_id.holding_company_id', '!=', company.id),
            ('company_id', '=', company.id),
            ('state', '=', 'done'),
            ('invoice_state', '=', '2binvoiced')
        ])
        return new_domain

    @api.model
    def _get_holding_invoice_domain(self, domain, company):
        new_domain = domain[:] if domain is not None else []
        new_domain.extend([
            ('group_id.holding_company_id', '=', company.id),
            ('company_id', '!=', company.id),
            ('state', '=', 'done'),
            ('holding_invoice_state', '=', '2binvoiced')
        ])
        return new_domain

    @api.multi
    def _scheduler_action_invoice_create(self, domain=None):
        companies = self.env['res.company'].search([])
        for company in companies:
            new_domain = self._get_invoice_domain(domain, company)
            picking = self.search(new_domain)
            if picking:
                self = self.browse(picking.ids)
                self.with_context(
                    holding_invoice=False,
                    force_company=company.id).action_invoice_create(
                        journal_id=False, group=True, type='out_invoice')

    @api.multi
    def _scheduler_action_holding_invoice_create(self, domain=None):
        companies = self.env['res.company'].search([])
        for company in companies:
            new_domain = self._get_holding_invoice_domain(domain, company)
            holding_picking = self.search(new_domain)
            if holding_picking:
                holding_picking.with_context(
                    holding_invoice=True,
                    force_company=company.id).action_invoice_create(
                        journal_id=False, group=True, type='out_invoice')


class StockMove(models.Model):
    _inherit = "stock.move"

    holding_invoice_state = fields.Selection([
        ('invoiced', 'Invoiced'),
        ('2binvoiced', 'To Be Invoiced'),
        ('none', 'Not Applicable')
    ], string='Holding Invoice Control', default='none')

    @api.model
    def _link_invoice_to_picking(self, move, inv_line_id, invoice_line_vals):
        holding_invoice = self._context.get('holding_invoice', False)
        if holding_invoice:
            move.write({'invoice_line_id': inv_line_id,
                        'holding_invoice_state': 'invoiced'})
            move.picking_id.write({
                'holding_invoice_id': invoice_line_vals['invoice_id'],
                'holding_invoice_state': 'invoiced',
                })
            return inv_line_id
        else:
            super(StockMove, self)._link_invoice_to_picking(
                move, inv_line_id, invoice_line_vals)

    @api.multi
    def _prepare_product_onchange_params(self, move, inv_line_vals):
        return [
            (move.product_id.id, move.product_uom.id),
            {
                'qty': inv_line_vals['quantity'],
                'name': '',
                'type': 'out_invoice',
                'partner_id': move.partner_id.id,
                'fposition_id': False,
                'price_unit': inv_line_vals['price_unit'],
                'currency_id': False,
                'company_id': False
            }]

    @api.multi
    def _merge_product_onchange(self, move, onchange_vals, inv_line_vals):
        holding_invoice = self._context.get('holding_invoice', False)
        if onchange_vals.get('account_id'):
            inv_line_vals['account_id'] = onchange_vals.get('account_id')
        if onchange_vals.get('invoice_line_tax_id'):
            inv_line_vals['invoice_line_tax_id'] = [[6, 0, onchange_vals.get(
                'invoice_line_tax_id')]]
        if not holding_invoice and move.picking_id.holding_company_id:
            inv_line_vals['discount'] = (move.picking_id.section_id.
                                         holding_discount)

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        inv_line_vals = super(StockMove, self)._get_invoice_line_vals(
            move, partner, inv_type)
        args, kwargs = self._prepare_product_onchange_params(
            move, inv_line_vals)
        onchange_vals = self.env['account.invoice.line'].product_id_change(
            *args, **kwargs)
        self._merge_product_onchange(
            move, onchange_vals['value'], inv_line_vals)
        return inv_line_vals

    @api.model
    def _get_master_data(self, move, company):
        partner, uid, currency = super(StockMove, self)._get_master_data(
            move, company)
        holding_invoice = self._context.get('holding_invoice', False)
        if move.picking_id.holding_company_id and not holding_invoice:
            partner = move.picking_id.holding_company_id.partner_id
        else:
            partner = move.picking_id.sale_id.partner_invoice_id
        return partner, uid, currency


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    holding_invoice_state = fields.Selection([
        ('invoiced', 'Invoiced'),
        ('2binvoiced', 'To Be Invoiced'),
        ('none', 'Not Applicable')
    ], string='Holding Invoice Control', default='none')

    @api.model
    def _run_move_create(self, procurement):
        res = super(ProcurementOrder, self)._run_move_create(procurement)
        res.update({'holding_invoice_state': procurement.invoice_state})
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    section_id = fields.Many2one('crm.case.section', string='Sales Team',
                                 readonly=True)
    holding_company_id = fields.Many2one(
        'res.company', string='Holding Company for Invoicing', readonly=True)
    holding_customer_automatic_invoice = fields.Boolean(
        string='Automatic invoice for holding customer', readonly=True)
    holding_supplier_automatic_invoice = fields.Boolean(
        string='Automatic invoice for holding supplier', readonly=True)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    holding_picking_ids = fields.One2many(
        'stock.picking', 'holding_invoice_id',
        string='Related Pickings', readonly=True,
        help="Related pickings(only when the holding invoice "
        "has been generated from the picking).")

    @api.multi
    def unlink(self):
        holding_picking_ids = []
        picking_ids = []
        for invoice in self:
            holding_picking_ids += invoice.holding_picking_ids
            picking_ids += invoice.picking_ids
        res = super(AccountInvoice, self).unlink()
        if res:
            for picking in holding_picking_ids:
                for move in picking.move_lines:
                    move.write({'holding_invoice_state': '2binvoiced'})
            for picking in picking_ids:
                for move in picking.move_lines:
                    move.write({'invoice_state': '2binvoiced'})
        return res
