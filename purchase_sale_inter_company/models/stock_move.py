# Copyright 2023 ForgeFlow <http://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_intercompany_move = fields.Boolean(
        string="Is Inter Company Move?", default=False, readonly=True, copy=False
    )
