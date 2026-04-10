# Copyright 2021 Camptocamp
# Copyright 2022 Akretion (Florian Mounier <florian.mounier@akretion.com>)
# Copyright 2023 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    intercompany_in_type_id = fields.Many2one(
        "stock.picking.type",
        string="Intercompany Reception Type",
        help="Operation type used to create the counterpart reception in this company "
        "when a delivery is validated in another company.",
    )
    intercompany_out_type_id = fields.Many2one(
        "stock.picking.type",
        string="Intercompany Delivery Type",
        help="Operation type used to create the counterpart delivery in this company "
        "when a reception is validated in another company.",
    )
    intercompany_picking_creation_mode = fields.Selection(
        selection=[
            ("in", "Reception Only"),
            ("out", "Delivery Only"),
            ("both", "Create Both"),
        ],
        default="in",
        help="Controls which counterpart pickings are automatically created "
        "for this company when a transfer is validated in another company:\n"
        "  - Reception Only: create a reception when a delivery is done "
        "in another company (default).\n"
        "  - Delivery Only: create a delivery when a reception is done "
        "in another company (manual action or scheduled action).\n"
        "  - Create Both: create both a reception and a delivery depending "
        "on the direction of the validated transfer.\n"
        "  - (empty): do not create any counterpart picking.",
    )
    intercompany_sync_qty_done = fields.Boolean(
        string="Sync Done Quantities",
        help="When enabled, the quantities done on the origin picking are "
        "automatically copied to the counterpart picking move lines upon "
        "counterpart creation.",
    )
    intercompany_share_lot = fields.Boolean(
        string="Share Lots / Serial Numbers",
        help="When enabled, lots and serial numbers used on the origin picking "
        "are made company-independent (company_id removed) so they are "
        "automatically visible and reusable in the destination company.\n"
        "This avoids duplicating traceability records across companies.",
    )
