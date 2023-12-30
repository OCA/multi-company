# Copyright (C) 2023 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    intercompany_out_type_id = fields.Many2one(
        related="company_id.intercompany_out_type_id", readonly=False
    )
    auto_update_qty_done = fields.Boolean(
        related="company_id.auto_update_qty_done", readonly=False
    )
    move_packages = fields.Boolean(related="company_id.move_packages", readonly=False)
    mirror_lot_numbers = fields.Boolean(
        related="company_id.mirror_lot_numbers", readonly=False
    )
