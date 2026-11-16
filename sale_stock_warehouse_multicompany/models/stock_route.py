# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockRoute(models.Model):
    _inherit = "stock.route"

    company_ids = fields.Many2many(
        "res.company",
        string="Companies",
        compute="_compute_company_ids",
        store=True,
        readonly=False,
    )

    def _compute_company_ids(self):
        for route in self:
            route.company_ids = [(6, 0, route.company_id.ids)]
