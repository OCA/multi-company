# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_sale_order_data(
        self, name, partner, dest_company, direct_delivery_address
    ):
        new_order = super()._prepare_sale_order_data(
            name, partner, dest_company, direct_delivery_address
        )
        delivery_address = (
            direct_delivery_address
            or self.picking_type_id.warehouse_id.partner_id
            or False
        )
        if delivery_address:
            new_order.update({"partner_shipping_id": delivery_address.id})
        warehouse = (
            dest_company.warehouse_id.company_id == dest_company
            and dest_company.warehouse_id
            or False
        )
        if warehouse:
            new_order.update({"warehouse_id": warehouse.id})
        return new_order
