# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class SaleOrder(models.Model):

    _inherit = "sale.order"

    auto_purchase_order_id = fields.Many2one('purchase.order',
                                             string='Source Purchase Order',
                                             readonly=True, copy=False)

    @api.multi
    def multi_company_check_prices(self, update=False):
        """ Compare prices of multi company orders with the originating
        purchase orders. """
        self.ensure_one()
        cur = self.pricelist_id.currency_id
        diffs = []
        for line in self.order_line.filtered('auto_purchase_line_id'):
            po_line = line.auto_purchase_line_id.sudo()
            if not cur.is_zero(po_line.price_unit - line.price_unit):
                diffs.append(
                    (po_line.name, po_line.price_unit, line.price_unit))
                if update:
                    po_line.write({'price_unit': line.price_unit})
        return diffs

    @api.multi
    def signal_workflow(self, signal):
        """ Check price differences with the origin purchase order and either
        report on the po that they were updated or raise an error (depending
        on the sale's company settings) """
        if signal == 'order_confirm':
            for order in self.filtered('auto_purchase_order_id'):
                po = order.auto_purchase_order_id.sudo()
                update = order.company_id.update_intercompany_purchase_price
                diffs = order.multi_company_check_prices(update=update)
                if not diffs:
                    continue
                if not update:
                    prices = '\n'.join(
                        _('%s: %s (PO) vs. %s (SO)') % diff for diff in diffs)
                    raise UserError(_(
                        'Could not confim sale order %s because there '
                        'were price differences with purchase order %s: %s'
                    ) % (order.name, po.name, prices))
                prices = '\n'.join(
                    _('%s: %s -> %s') % diff for diff in diffs)
                po.message_post(_(
                    'Sale order %s was confirmed. The following prices '
                    'were updated on this purchase order: %s') % (
                        order.name, prices))
        return super(SaleOrder, self).signal_workflow(signal=signal)


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        'purchase.order.line', string='Source Purchase Order Line',
        readonly=True, copy=False)
