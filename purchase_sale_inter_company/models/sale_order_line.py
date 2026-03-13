# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Source Purchase Order Line",
        readonly=True,
        copy=False,
    )

    def _intercompany_update_purchase_line_price(self):
        """Writes the net price (price_unit after discount) to the purchase line.

        Can be inherited in other modules to change the behavior, for example
        if discounts are available in the purchase order.
        """
        self.ensure_one()
        self.auto_purchase_line_id.price_unit = self.price_unit * (
            1 - self.discount / 100
        )
