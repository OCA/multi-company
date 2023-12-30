# Copyright (C) 2023 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    intercompany_out_type_id = fields.Many2one(
        "stock.picking.type", string="Intercompany Operation Type OUT"
    )
    intercompany_in_type_id = fields.Many2one(string="Intercompany Operation Type IN")
    auto_update_qty_done = fields.Boolean(
        string="Set Qty Done",
        help="Enable 'Set Qty Done' to automatically update "
        "the 'Done' quantity based on the counterpart picking.",
    )
    move_packages = fields.Boolean(
        help="Enable 'Move Packages' to automatically use the same package "
        "for the incoming operation as was used for the outgoing one."
    )
    mirror_lot_numbers = fields.Boolean(
        string="Mirror Lots/Serial Numbers",
        help="Enable 'Mirror Lots/Serial Numbers' if you want lots to create assign "
        "lots/serial numbers with the same names in the destination company automatically.",
    )
