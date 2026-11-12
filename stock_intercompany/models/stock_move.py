# Copyright 2021 Camptocamp
# Copyright 2022 Akretion (Florian Mounier <florian.mounier@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    intercompany_origin_move_id = fields.Many2one(
        "stock.move",
        check_company=False,
        help="Move in another company that originated this counterpart move.",
    )

    def _search_picking_for_assignation_domain(self):
        """Exclude pickings that already have an intercompany counterpart
        so that new moves are not accidentally merged into a locked picking."""
        domain = super()._search_picking_for_assignation_domain()
        domain += [("has_counterpart", "=", False)]
        return domain
