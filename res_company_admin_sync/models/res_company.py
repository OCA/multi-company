# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        admins = (
            self.env["res.users"]
            .sudo()
            .search([("group_ids", "in", self.env.ref("base.group_system").id)])
        )
        if admins:
            admins.write(
                {"company_ids": [Command.link(company.id) for company in companies]}
            )
        return companies
