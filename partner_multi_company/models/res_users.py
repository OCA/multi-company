# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html.html

from odoo import Command, api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        for user in users:
            user.partner_id.company_ids = user.company_ids
        return users

    def write(self, vals):
        res = super(ResUsers, self.with_context(from_res_users=True)).write(vals)
        if "company_ids" in vals:
            for user in self.sudo():
                commands = []
                company_ids_data = vals["company_ids"]
                if isinstance(company_ids_data, list) and user.partner_id.company_ids:
                    for item in company_ids_data:
                        if isinstance(item, (list | tuple)):
                            if item[0] == Command.LINK:
                                commands.append(item)
                            if item[0] == Command.SET:
                                for company_id in item[2]:
                                    commands.append(Command.link(company_id))
                        else:
                            commands.append(Command.link(item))
                    user.partner_id.company_ids = commands
        return res
