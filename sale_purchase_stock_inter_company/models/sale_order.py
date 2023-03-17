# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_purchase_order_data(self, name, partner, dest_company):
        new_order = super()._prepare_purchase_order_data(name, partner, dest_company)
        warehouse = (
            dest_company.warehouse_id.company_id == dest_company
            and dest_company.warehouse_id
            or False
        )
        if warehouse:
            new_order.update({"picking_type_id": warehouse.in_type_id.id})
        return new_order
