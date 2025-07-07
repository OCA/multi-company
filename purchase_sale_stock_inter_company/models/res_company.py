# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

SELECTION_SYNC_FAILURE_ACTIONS = [
    ("raise", "Block and raise error"),
    ("notify", "Continue, but create activity to notify someone"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse For Sale Orders",
        help="Default value to set on Sale Orders that "
        "will be created based on Purchase Orders made to this company",
    )
    sync_picking = fields.Boolean(
        string="Sync the receipt with the delivery",
        help="Sync the receipt from the destination company with the "
        "delivery from the source company",
    )
    sync_picking_failure_action = fields.Selection(
        SELECTION_SYNC_FAILURE_ACTIONS,
        string="On sync picking failure",
        default="raise",
        help="Pick action to perform on sync picking failure",
    )
    block_po_manual_picking_validation = fields.Boolean(
        string="Block manual validation of picking in the destination company",
    )
    notify_user_id = fields.Many2one("res.users", "User to Notify")
