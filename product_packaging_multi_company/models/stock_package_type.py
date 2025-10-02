# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPackageType(models.Model):
    _inherit = ["multi.company.abstract", "stock.package.type"]
    _name = "stock.package.type"
    _description = "Package Type (Multi-Company)"
