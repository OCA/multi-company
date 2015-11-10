# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2015 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, fields, api
from openerp.exceptions import Warning as UserError
from collections import defaultdict
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    company_sale_ids = fields.One2many('sale.order', 'holding_company_id')
    holding_sale_ids = fields.One2many('sale.order', 'holding_invoice_id')
    holding_sale_count = fields.Integer(
        compute='_holding_sale_count', string='# of Sales Order')
    sale_count = fields.Integer(
        compute='_sale_count', string='# of Sales Order')
    child_invoice_ids = fields.One2many(
        'account.invoice', 'holding_invoice_id')
    child_invoice_count = fields.Integer(
        compute='_child_invoice_count', string='# of Invoice')
    holding_invoice_id = fields.Many2one('account.invoice')

    @api.multi
    def _holding_sale_count(self):
        for inv in self:
            inv.holding_sale_count = len(inv.holding_sale_ids)

    @api.multi
    def _sale_count(self):
        for inv in self:
            inv.sale_count = len(inv.sale_ids)

    @api.multi
    def _child_invoice_count(self):
        for inv in self:
            inv.child_invoice_count = len(inv.child_invoice_ids)

    @api.multi
    def unlink(self):
        sale_obj = self.env['sale.order']
        sales = sale_obj.search([('holding_invoice_id', 'in', self.ids)])
        res = super(AccountInvoice, self).unlink()
        #We use an SQL request here for solving perf issue
        if sales:
            self._cr.execute("""UPDATE sale_order
                SET holding_invoice_state = '2binvoiced'
                WHERE id in %s""", (tuple(sales.ids),))
        return res

    @api.multi
    def generate_child_invoice(self):
        invoices = self.browse(False)
        for company in self.env['res.company'].search([]):
            sales = self.env['sale.order']\
                .with_context(force_company=company.id, from_holding=True)\
                .search([
                    ('holding_invoice_id', '=', self.id),
                    ('company_id', '=', company.id),
                    ])
            if sales:
                invoices |= sales.action_child_invoice()
                # Dummy call to workflow, will not create another invoice
                # but bind the new invoice to the subflow
                sales.signal_workflow('manual_invoice')
        return True


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sale_line_ids = fields.Many2many(
        comodel_name='account.invoice.line',
        relation='sale_order_line_invoice_rel',
        column1='invoice_id',
        column2='order_line_id')
