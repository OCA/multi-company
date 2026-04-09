# Copyright 2022 Akretion
# @author Florian Mounier <florian.mounier@akretion.com>
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _create_counterpart_picking(self):
        """Prevent stock_intercompany from creating a duplicate incoming picking
        when purchase_sale_stock_inter_company already handles the receipt
        synchronization for this delivery.

        purchase_sale_stock_inter_company takes over when the delivery is linked
        to a sale order that was generated from an inter-company purchase order
        (i.e. _is_intercompany_delivery() is True).  In that case the receipt
        in the destination company is managed through the PO/SO document pair
        and stock_intercompany must not create an additional one.
        """
        if self._is_intercompany_delivery():
            return self.env["stock.picking"]
        return super()._create_counterpart_picking()
