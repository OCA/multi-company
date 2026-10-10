# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def write(self, vals):
        result = super().write(vals)
        if "group_ids" in vals:
            admin_group = self.env.ref("base.group_system")
            admins = self.filtered(lambda user: admin_group in user.group_ids)
            if admins:
                # Small table (one row per company); loading it all is fine.
                companies = self.env["res.company"].sudo().search([])  # pylint: disable=no-search-all
                admins.write(
                    {"company_ids": [Command.link(company.id) for company in companies]}
                )
        return result
