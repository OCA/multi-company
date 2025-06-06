# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    intercompany_create_lots_mode = fields.Selection(
        [("same", "Use Same Number"), ("manual", "Assign Number Manually")],
        string="Lots Creation Mode in Intercompany",
        default="same",
        required=True,
        help=" Select which logic to follow when a receipt with products "
        "tracked by Lots/Serial numbers is auto validated by an intercompany flow:\n"
        "* Use Same Number: Create a Lot/Serial number with the same number as in the "
        "originating company.\n"
        "* Assign Number Manually: Assign manually in the receipt the lot number to be used.\n",
    )
