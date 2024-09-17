# Copyright (C) 2024-Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._propagate_access_to_child_companies()
        return users

    def write(self, vals):
        res = super().write(vals)
        if vals.get("company_ids", False):
            self._propagate_access_to_child_companies()
        return res

    def _propagate_access_to_child_companies(self):
        """If a user has access to a parent company, so he'll have
        access to all the child companies"""

        def _get_recursive_child_companies(self, companies):
            result = companies.child_ids
            if companies.child_ids.child_ids:
                result |= _get_recursive_child_companies(self, companies.child_ids)
            return result

        for user in self:
            existing_companies = user.company_ids
            all_companies = _get_recursive_child_companies(self, existing_companies)

            new_company_ids = list(set(all_companies.ids) - set(existing_companies.ids))
            if new_company_ids:
                super(ResUsers, user).write(
                    {"company_ids": [Command.link(x) for x in new_company_ids]}
                )
        return
