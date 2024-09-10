# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InterCompanyRulesConfig(models.TransientModel):
    _inherit = "res.config.settings"

    so_from_po = fields.Boolean(
        related="company_id.so_from_po",
        string="Create Sale Orders when buying to this company",
        help="Generate a Sale Order when a Purchase Order with this company "
        "as supplier is created.\n The intercompany user must at least be "
        "Sale User.",
        readonly=False,
    )
    sale_auto_validation = fields.Boolean(
        related="company_id.sale_auto_validation",
        string="Sale Orders Auto Validation",
        help="When a Sale Order is created by a multi company rule for "
        "this company, it will automatically validate it.",
        readonly=False,
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        related="company_id.warehouse_id",
        string="Warehouse for Sale Orders",
        help="Default value to set on Sale Orders that will be created "
        "based on Purchase Orders made to this company.",
        readonly=False,
    )
    intercompany_sale_user_id = fields.Many2one(
        comodel_name="res.users",
        related="company_id.intercompany_sale_user_id",
        string="Intercompany Sale User",
        help="User used to create the sales order arising from a purchase "
        "order in another company.",
        readonly=False,
    )
    sync_picking = fields.Boolean(
        related="company_id.sync_picking",
        string="Sync the receipt from the destination company with the delivery",
        help="Sync the receipt from the destination company with "
        "the delivery from the source company",
        readonly=False,
    )
    sync_picking_failure_action = fields.Selection(
        related="company_id.sync_picking_failure_action",
    sync_picking_state = fields.Boolean(
        related="company_id.sync_picking_state",
        readonly=False,
    )
    block_po_manual_picking_validation = fields.Boolean(
        related="company_id.block_po_manual_picking_validation",
        readonly=False,
    )
    notify_user_id = fields.Many2one(
        "res.users",
        related="company_id.notify_user_id",
        help="User to notify incase of sync picking failure.",
        readonly=False,
    )
