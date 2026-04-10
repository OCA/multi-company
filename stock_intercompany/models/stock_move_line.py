# Copyright 2021 Camptocamp
# Copyright 2026 Akretion (Guillaume Masson <guillaume.masson@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    intercompany_origin_line_id = fields.Many2one(
        "stock.move.line",
        check_company=False,
        help="Move line in another company that originated this counterpart line.",
    )
