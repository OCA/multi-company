# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sync_picking_transit_receipt = fields.Boolean(
        string="Sync the transit receipt with the delivery",
        help="Purchases from a company of the group are received through the "
        "incoming transit: the delivery of the source company validates the "
        "transit receipt, the warehouse validates the reception.",
    )
