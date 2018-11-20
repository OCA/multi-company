# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    auto_purchase_order_id = fields.Many2one('purchase.order',
                                             string='Source Purchase Order',
                                             readonly=True, copy=False)

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.auto_purchase_order_id:
                for line in order.order_line:
                    if line.auto_purchase_line_id:
                        line.auto_purchase_line_id.sudo().write({
                            'price_unit': line.price_unit})
        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        'purchase.order.line', string='Source Purchase Order Line',
        readonly=True, copy=False)
