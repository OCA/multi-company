# -*- coding: utf-8 -*-
from openerp import fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    auto_generated = fields.Boolean(string='Auto Generated Sale Order',
                                    readonly=True, copy=False)
    auto_purchase_order_id = fields.Many2one('purchase.order',
                                             string='Source Purchase Order',
                                             readonly=True, copy=False)


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        'purchase.order.line', string='Source Purchase Order Line',
        readonly=True, copy=False)
