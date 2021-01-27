# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class PosCategory(models.Model):
    _inherit = ["multi.company.abstract", "pos.category"]
    _name = "pos.category"
