# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InterCompanyRulesConfig(models.TransientModel):

    _inherit = "res.config.settings"

    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        related="company_id.warehouse_id",
        string="Warehouse for Purchase Orders",
        help="Default value to set on Purchase Orders that will be created "
        "based on Sale Orders made to this company.",
        readonly=False,
    )
