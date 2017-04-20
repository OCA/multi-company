# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    auto_purchase_order_id = fields.Many2one('purchase.order',
                                             string='Source Purchase Order',
                                             readonly=True, copy=False)

    @api.multi
    def signal_workflow(self, signal):
        for order in self:
            if signal == 'order_confirm' and order.auto_purchase_order_id:
                for line in order.order_line:
                    if line.auto_purchase_line_id:
                        line.auto_purchase_line_id.sudo().write({
                            'price_unit': line.price_unit})
        return super(SaleOrder, self).signal_workflow(signal=signal)


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        'purchase.order.line', string='Source Purchase Order Line',
        readonly=True, copy=False)
