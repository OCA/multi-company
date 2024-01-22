# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    route_id = fields.Many2one(
        "stock.route", domain="[('company_ids', 'in', company_id)]"
    )
