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
from openerp.addons.stock_account.stock import stock_move

ori_view_init = stock_invoice_onshipping.view_init
ori_create_invoice_line_from_vals = stock_move._create_invoice_line_from_vals


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

    @api.multi
    def action_invoice_create(
            self, journal_id, group=False, type='out_invoice'):
        active_ids = self._context.get('active_ids', [])
        holding_active_ids = self._context.get('holding_active_ids', [])
        invoice_ids = []
        if active_ids:
            todo = {}
            for picking in self.browse(active_ids):
                if picking.holding_company_id:
                    partner = picking.holding_company_id.partner_id
                else:
                    partner = picking.sale_id.partner_invoice_id
                #grouping is based on the invoiced partner
                if group:
                    key = partner
                else:
                    key = picking.id
                for move in picking.move_lines:
                    if move.invoice_state == '2binvoiced':
                        if (move.state != 'cancel') and not move.scrapped:
                            todo.setdefault(key, [])
                            todo[key].append(move)
            for moves in todo.values():
                invoice_ids += self._invoice_create_line(
                    moves, journal_id, type)
                for move in moves:
                    invoice = move.invoice_line_id.invoice_id
                    picking = move.picking_id
                    picking.write({'invoice_id': invoice.id})
        if holding_active_ids:
            todo = {}
            for picking in self.browse(holding_active_ids):
                partner = picking.sale_id.partner_invoice_id
                #grouping is based on the invoiced partner
                if group:
                    key = partner
                else:
                    key = picking.id
                for move in picking.move_lines:
                    if move.holding_invoice_state == '2binvoiced':
                        if (move.state != 'cancel') and not move.scrapped:
                            todo.setdefault(key, [])
                            todo[key].append(move)
            for moves in todo.values():
                invoice_ids += self.with_context(
                    holding_invoice=True)._invoice_create_line(
                        moves, journal_id, type)
                for move in moves:
                    holding_invoice = move.invoice_line_id.invoice_id
                    picking = move.picking_id
                    picking.write({'holding_invoice_id': holding_invoice.id})
        return invoice_ids

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        vals = super(StockPicking, self)._get_invoice_vals(
            key, inv_type, journal_id, move)
        account = self.env['account.account'].browse(vals['account_id'])
        if account.company_id.id != vals['company_id']:
            vals['account_id'] = move.partner_id.property_account_receivable.id
        return vals

    @api.model
    def _invoice_create_line(self, moves, journal_id, inv_type='out_invoice'):
        invoice_obj = self.env['account.invoice']
        move_obj = self.env['stock.move']
        holding_invoice = self._context.get('holding_invoice', False)
        user_id = self._context.get('uid', False)
        user = self.env['res.users'].browse(self._context['uid'])
        if holding_invoice:
            invoices = {}
            for move in moves:
                company = user.company_id
                currency_id = company.currency_id.id
                partner = move.picking_id.sale_id.partner_invoice_id
                key = (partner, currency_id, company.id, user_id)
                journal_ids = self.env['account.journal'].search([
                    ('type', '=', 'sale'),
                    ('company_id', '=', company.id)
                ])
                invoice_vals = self._get_invoice_vals(
                    key, inv_type, journal_ids[0].id, move)
                invoice_vals['user_id'] = user_id

                if key not in invoices:
                    # Get account and payment terms
                    invoice_id = self._create_invoice_from_picking(
                        move.picking_id, invoice_vals)
                    invoices[key] = invoice_id
                else:
                    invoice = self.env['account.invoice'].browse(invoices[key])
                    if not invoice.origin or (invoice_vals['origin'] not in
                                              invoice.origin.split(', ')):
                        invoice_origin = filter(
                            None, [invoice.origin, invoice_vals['origin']])
                        invoice.write({'origin': ', '.join(invoice_origin)})
                origin = move.picking_id.name
                invoice_line_vals = move_obj._get_invoice_line_vals(
                    move, partner, inv_type)
                invoice_line_vals['invoice_id'] = invoices[key]
                invoice_line_vals['origin'] = origin
                move_obj._create_invoice_line_from_vals(
                    move, invoice_line_vals)
                move.write({'holding_invoice_state': 'invoiced'})
            invoice_obj.button_compute(
                set_total=(inv_type in ('in_invoice', 'in_refund')))
            invoice_values = invoices.values()
        else:
            invoices = {}
            for move in moves:
                company = move.picking_id.company_id
                currency_id = company.currency_id.id
                if move.picking_id.holding_company_id:
                    partner = move.picking_id.holding_company_id.partner_id
                else:
                    partner = move.picking_id.sale_id.partner_invoice_id
                key = (partner, currency_id, company.id, user_id)
                journal_ids = self.env['account.journal'].search([
                    ('type', '=', 'sale'),
                    ('company_id', '=', company.id)
                ])
                invoice_vals = self._get_invoice_vals(
                    key, inv_type, journal_ids[0].id, move)
                invoice_vals['user_id'] = user_id

                if key not in invoices:
                    # Get account and payment terms
                    invoice_id = self._create_invoice_from_picking(
                        move.picking_id, invoice_vals)
                    invoices[key] = invoice_id
                else:
                    invoice = self.env['account.invoice'].browse(invoices[key])
                    if not invoice.origin or (invoice_vals['origin'] not in
                                              invoice.origin.split(', ')):
                        invoice_origin = filter(
                            None, [invoice.origin, invoice_vals['origin']])
                        invoice.write({'origin': ', '.join(invoice_origin)})
                origin = move.picking_id.name
                invoice_line_vals = move_obj._get_invoice_line_vals(
                    move, partner, inv_type)
                invoice_line_vals['invoice_id'] = invoices[key]
                invoice_line_vals['origin'] = origin
                move_obj._create_invoice_line_from_vals(
                    move, invoice_line_vals)
                move.write({'invoice_state': 'invoiced'})
            invoice_obj.button_compute(
                set_total=(inv_type in ('in_invoice', 'in_refund')))
            invoice_values = invoices.values()
        return invoice_values

    def _get_domains(self, vals):
        vals = {
            'pickings': [
                ('state', '=', 'done'),
                ('invoice_state', '=', '2binvoiced')
            ],
            'holding_pickings': [
                ('state', '=', 'done'),
                ('holding_invoice_state', '=', '2binvoiced')
            ]
        }
        return vals

    @api.multi
    def _scheduler_action_invoice_create(self):
        domains = {}
        domains = self._get_domains(domains)
        pickings = self.search(domains['pickings'])
        holding_pickings = self.search(domains['holding_pickings'])
        picking_ids = []
        holding_picking_ids = []
        for picking in pickings:
            if (picking.sale_id.section_id.holding_supplier_automatic_invoice
                    and picking.invoice_state == '2binvoiced'
                    and picking.company_id != picking.sale_id.section_id.holding_company_id):
                picking_ids.append(picking.id)
        for picking in holding_pickings:
            if (picking.sale_id.section_id.holding_customer_automatic_invoice
                    and picking.holding_invoice_state == '2binvoiced'):
                holding_picking_ids.append(picking.id)
        self.with_context(
            holding_active_ids=holding_picking_ids,
            active_ids=picking_ids).action_invoice_create(
                journal_id=False, group=True, type='out_invoice')


class StockMove(models.Model):
    _inherit = "stock.move"

    holding_invoice_state = fields.Selection([
        ('invoiced', 'Invoiced'),
        ('2binvoiced', 'To Be Invoiced'),
        ('none', 'Not Applicable')
    ], string='Holding Invoice Control', default='none')

    @api.model
    def _create_invoice_line_from_vals(self, move, invoice_line_vals):
        invoice = self.env['account.invoice'].browse(
            invoice_line_vals['invoice_id'])
        account_obj = self.env['account.account']
        tax_obj = self.env['account.tax']
        account = account_obj.browse(invoice_line_vals['account_id'])
        if account.company_id != invoice.company_id:
            account = account_obj.search([
                ('code', '=', account.code),
                ('company_id', '=', invoice.company_id.id)
            ])
            invoice_line_vals['account_id'] = account.id
        if invoice_line_vals['invoice_line_tax_id'][0][2]:
            tax = tax_obj.browse(
                invoice_line_vals['invoice_line_tax_id'][0][2][0])
            if tax.company_id != invoice.company_id:
                tax = tax_obj.search([
                    ('type_tax_use', '=', tax.type_tax_use),
                    ('type', '=', tax.type),
                    ('amount', '=', tax.amount),
                    ('company_id', '=', invoice.company_id.id)
                ])
                invoice_line_vals['invoice_line_tax_id'][0][2][0] = tax.id
        inv_line_id = ori_create_invoice_line_from_vals(
            self, move, invoice_line_vals)
        move.write({'invoice_line_id': inv_line_id})
        holding_invoice = self._context.get('holding_invoice', False)
        if holding_invoice:
            picking = move.picking_id
            picking.holding_invoice_id = invoice_line_vals['invoice_id']
        else:
            move.picking_id.invoice_id = invoice_line_vals['invoice_id']
        return inv_line_id

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        vals = super(StockMove, self)._get_invoice_line_vals(
            move, partner, inv_type)
        account = self.env['account.account'].browse(vals['account_id'])
        if account.company_id != move.company_id:
            account_id = move.product_id.property_account_income.id
            if not account_id:
                account_id = (move.product_id.categ_id.
                              property_account_income_categ.id)
            vals['account_id'] = account_id
        return vals


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
