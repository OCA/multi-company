# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        """When completing a sales receipt (return) picking, if the destination location
        is inter-company (because it is an inter-company process), the system will
        automatically create a sales order line; however, this would be incorrect.
        Therefore, we use the context added in _action_done() in stock.picking to
        prevent this.
        Related to https://github.com/odoo/odoo/blob/ee5502ef5ebe7c3a87984697771643d1f798b880/addons/sale_stock/models/stock.py#L141
        """
        if self.env.context.get("rma_inter_company_picking_action_done"):
            vals_list = []
        return super().create(vals_list)
