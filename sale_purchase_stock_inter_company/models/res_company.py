# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse For Purchase Orders",
        help="Default value to set on Purchase Orders that "
        "will be created based on Sale Orders made to this company",
    )
