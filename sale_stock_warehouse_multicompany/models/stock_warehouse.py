# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Warehouse(models.Model):
    _inherit = ["multi.company.abstract", "stock.warehouse"]
    _name = "stock.warehouse"
