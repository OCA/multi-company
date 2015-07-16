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

from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    holding_company_id = fields.Many2one(
        'res.company',
        related='section_id.holding_company_id',
        string='Holding Company for Invoicing', readonly=True)

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        vals = super(SaleOrder, self)._prepare_order_line_procurement(
            order=order, line=line, group_id=group_id)
        vals['holding_invoice_state'] = ((order.order_policy == 'picking') and
                                         '2binvoiced')
        return vals

    @api.model
    def _prepare_procurement_group(self, order):
        res = super(SaleOrder, self)._prepare_procurement_group(order)
        res.update({
            'section_id': order.section_id.id,
            'holding_company_id': order.section_id.holding_company_id.id,
            'holding_customer_automatic_invoice': (
                order.section_id.holding_customer_automatic_invoice),
            'holding_supplier_automatic_invoice': (
                order.section_id.holding_supplier_automatic_invoice),
        })
        return res

    @api.onchange('section_id', 'holding_company_id')
    def onchange_section_id(self):
        if self.section_id and self.holding_company_id:
            self.order_policy = 'picking'
        else:
            self.order_policy = 'manual'

    @api.multi
    def write(self, values):
        section_id = values.get('section_id', False)
        if section_id:
            section = self.env['crm.case.section'].browse(section_id)
            if section.holding_company_id:
                values.update({'order_policy': 'picking'})
        return super(SaleOrder, self).write(values)

    @api.model
    def create(self, values):
        section_id = values.get('section_id', False)
        if section_id:
            section = self.env['crm.case.section'].browse(section_id)
            if section.holding_company_id:
                values.update({'order_policy': 'picking'})
        return super(SaleOrder, self).create(values)
