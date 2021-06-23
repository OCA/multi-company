# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RestaurantTable(models.Model):
    _inherit = "restaurant.table"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="floor_id.company_id",
        index=True,
        store=True,
    )
