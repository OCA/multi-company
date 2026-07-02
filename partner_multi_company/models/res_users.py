# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html.html

from odoo import Command, api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        # Base ``res.users.create()`` syncs the partner's ``company_id``
        # mid-create ("if partner is global we keep it that way",
        # ``odoo/addons/base/models/res_users.py``) whenever the partner
        # already has a company -- an existing partner being promoted to
        # user, or any module putting a default on
        # ``res.partner.company_id`` (e.g. ``partner_company_default``).
        # That write fires the ``company_id`` inverse, which rewrites the
        # partner's ``company_ids`` down to a single company while the
        # user is only half-built, and ``_check_company_id`` would reject
        # that transient state before the alignment below ever runs. Skip
        # the constraint during the create; the alignment write below
        # re-triggers it on the final, consistent state.
        users = super(
            ResUsers, self.with_context(res_users_creation_in_progress=True)
        ).create(vals_list)
        users = users.with_context(res_users_creation_in_progress=False)
        for user in users:
            # The new user might have a company even if it was not in `vals`
            # because of defaults for example.
            if user.company_ids:
                user.partner_id.company_ids += user.company_ids
        return users

    def write(self, vals):
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
        return super(ResUsers, self.with_context(from_res_users=True)).write(vals)
