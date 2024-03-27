# Copyright 2023 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _inter_company_create_sale_order(self, dest_company):
        """We skip container deposit computation on SO since we are only copying
        the values from the PO"""
        self = self.with_context(skip_update_container_deposit=True)
        return super(PurchaseOrder, self)._inter_company_create_sale_order(dest_company)

    def _prepare_sale_order_line_data(self, purchase_line, dest_company, sale_order):
        order_line = super()._prepare_sale_order_line_data(
            purchase_line, dest_company, sale_order
        )
        # Copy value from PO to SO
        order_line["is_container_deposit"] = purchase_line.is_container_deposit
        return order_line

    def write(self, vals):
        # Allow update of so lines on locked sale on update of order container deposit quantity
        if self.env.context.get("update_order_container_deposit_quantity", False):
            self = self.with_context(allow_update_locked_sales=True)
        return super().write(vals)
