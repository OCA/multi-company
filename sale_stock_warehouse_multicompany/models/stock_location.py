# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRoute(models.Model):
    _inherit = ["multi.company.abstract", "stock.route"]
    _name = "stock.route"
