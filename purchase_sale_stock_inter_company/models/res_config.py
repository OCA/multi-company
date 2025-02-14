# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InterCompanyRulesConfig(models.TransientModel):

    _inherit = "res.config.settings"

    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        related="company_id.warehouse_id",
        string="Warehouse for Sale Orders",
        help="Default value to set on Sale Orders that will be created "
        "based on Purchase Orders made to this company.",
        readonly=False,
    )

    link_purchase_sale_picking = fields.Boolean(
        related="company_id.link_purchase_sale_picking",
        string="Link Purchase and Sale Pickings",
        help="If checked, the pickings of the purchase and sale "
        "orders will be linked together. This will validate "
        "the purchase pickings when the sale pickings are validated.",
        readonly=False,
    )
