# Copyright (C) 2024-Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies.mapped("parent_id").user_ids._propagate_access_to_child_companies()
        return companies

    def write(self, vals):
        res = super().write(vals)
        if vals.get("parent_id", False):
            self.mapped("parent_id").user_ids._propagate_access_to_child_companies()
        return res
