# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RestaurantFloor(models.Model):
    _inherit = "restaurant.floor"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        default=lambda self: self.env.user.company_id,
    )

    @api.onchange("pos_config_id")
    def _onchange_pos_config_id(self):
        if self.pos_config_id:
            self.company_id = self.pos_config_id.company_id

    @api.constrains("company_id", "pos_config_id")
    def _check_company_pos_config(self):
        for floor in self.filtered(lambda x: x.company_id and x.pos_config_id):
            if floor.company_id != floor.pos_config_id.company_id:
                raise UserError(_(
                    "Incorrect values for company and pos config"))
