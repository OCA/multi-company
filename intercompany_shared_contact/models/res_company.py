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
        self.check_access_rights("create")
        # We need to use sudo as the partner created will be linked
        # to the new company and this company is not yet added to the current user
        # so we are in a case of write/create on a partner where
        # the origin_company_id do not belong yet to the user
        return super(ResCompany, self.sudo()).create(vals_list)
