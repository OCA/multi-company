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
    sync_picking = fields.Boolean(
        related="company_id.sync_picking",
        string="Sync the receipt from the destination company with the delivery",
        help="Sync the receipt from the destination company with "
        "the delivery from the source company",
        readonly=False,
    )
    sync_picking_failure_action = fields.Selection(
        related="company_id.sync_picking_failure_action",
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
