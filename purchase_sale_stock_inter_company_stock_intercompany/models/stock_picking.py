# Copyright 2022 Akretion
# @author Florian Mounier <florian.mounier@akretion.com>
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _create_counterpart_picking(self, mode):
        """Prevent stock_intercompany from creating a duplicate incoming picking
        when purchase_sale_stock_inter_company already handles the receipt
        synchronization for this delivery.

        purchase_sale_stock_inter_company takes over when the delivery is linked
        to a sale order that was generated from an inter-company purchase order
        (i.e. _is_intercompany_delivery() is True).  In that case the receipt
        in the destination company is managed through the PO/SO document pair
        and stock_intercompany must not create an additional one.
        """
        if mode == "in" and self._is_intercompany_delivery():
            return self.env["stock.picking"]
        return super()._create_counterpart_picking(mode)

    def _check_intercompany_company(self, company, mode):
        """Prevent stock_intercompany from creating a delivery counterpart
        (mode 'out') when the reception picking is already managed by
        purchase_sale_stock_inter_company through a PO/SO document pair.

        A reception picking is managed by purchase_sale_stock_inter_company
        when it is linked to a purchase order that has a mirror sale order
        (intercompany_sale_order_id), meaning the full document flow is already
        tracked via the PO/SO pair.  In that case stock_intercompany must not
        create an additional outgoing counterpart on the vendor side.
        """
        if mode == "out" and self.purchase_id.sudo().intercompany_sale_order_id:
            return False
        return super()._check_intercompany_company(company, mode)

    def _remaining_out_counterpart_picking(self):
        """Extend the scheduled action to exclude reception pickings that
        are already managed by purchase_sale_stock_inter_company.

        Pickings linked to a PO that has a mirror SO (intercompany_sale_order_id)
        are handled by the PO/SO document flow and must not receive an additional
        delivery counterpart from the stock_intercompany scheduled action.
        """
        all_pickings = super()._remaining_out_counterpart_picking()
        filtered_pickings = all_pickings.filtered(
            lambda sp: not sp.purchase_id.intercompany_sale_order_id
        )
        return filtered_pickings
