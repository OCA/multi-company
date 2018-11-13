# Copyright 2018 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    company_id = fields.Many2one(
        related='move_id.company_id',
        store=True,
        readonly=True,
    )
