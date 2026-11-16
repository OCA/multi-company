# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    route_id = fields.Many2one(
        "stock.route",
        domain="[('company_ids', 'in', company_id),('sale_selectable','=', True)]",
        check_company=False,
    )

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id=group_id)
        # Procurements must be created in warehouse company
        if self.order_id.warehouse_id:
            values["company_id"] = self.order_id.warehouse_id.company_id
        return values
