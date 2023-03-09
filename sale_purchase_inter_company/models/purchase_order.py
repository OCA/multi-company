# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    auto_sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Source Sale Order",
        readonly=True,
        copy=False,
    )

    def button_approve(self, force=False):
        for order in self.filtered("auto_sale_order_id"):
            for line in order.order_line.sudo():
                if line.auto_sale_line_id:
                    line.price_unit = line.auto_sale_line_id.price_unit
        return super().button_approve(force)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    auto_sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Source Sale Order Line",
        readonly=True,
        copy=False,
    )
