# Copyright 2021 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    _sql_constraints = [
        (
            "partner_uniq",
            "unique (partner_id)",
            "The company partner_id must be unique !",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        self = self.with_context(creating_res_company=True)
        return super().create(vals_list).with_context(creating_res_company=False)
