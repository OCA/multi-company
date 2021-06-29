# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    auto_purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Source Purchase Order",
        readonly=True,
        copy=False,
    )

    def action_confirm(self):
        for order in self.filtered("auto_purchase_order_id"):
            for line in order.order_line.sudo():
                if line.auto_purchase_line_id:
                    line.auto_purchase_line_id.price_unit = line.price_unit
        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Source Purchase Order Line",
        readonly=True,
        copy=False,
    )
