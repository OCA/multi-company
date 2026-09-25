# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pricelist_id = fields.Many2one(
        domain="['|', '|', "
        "('company_id', '=', False), "
        "('company_id', '=', company_id), "
        "('company_ids', 'in', [company_id])]",
    )
