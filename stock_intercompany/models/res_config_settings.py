# Copyright 2021 Camptocamp
# Copyright 2022 Akretion (Florian Mounier <florian.mounier@akretion.com>)
# Copyright 2023 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    intercompany_in_type_id = fields.Many2one(
        related="company_id.intercompany_in_type_id", readonly=False
    )
    intercompany_out_type_id = fields.Many2one(
        related="company_id.intercompany_out_type_id", readonly=False
    )
    intercompany_picking_creation_mode = fields.Selection(
        related="company_id.intercompany_picking_creation_mode", readonly=False
    )
    intercompany_sync_qty_done = fields.Boolean(
        related="company_id.intercompany_sync_qty_done", readonly=False
    )
    intercompany_share_lot = fields.Boolean(
        related="company_id.intercompany_share_lot", readonly=False
    )
