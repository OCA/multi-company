# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.constrains("active")
    def _check_active(self):
        ResUsers = self.env["res.users"]

        for company in self:
            if not company.active:
                if self.env.user.company_id == company:
                    raise ValidationError(_("You can not disable the current company."))
                # check if it it the current company for some users
                users = ResUsers.search([("company_id", "=", company.id)])
                if len(users):
                    raise ValidationError(
                        _(
                            "You can not disable the company %(company_name)s because it is the"
                            " current company for the following active users:\n\n"
                            " - %(user_names)s\n\n"
                            " Please change the company of these users, or disable"
                            " them",
                            company_name=company.name,
                            user_names="\n - ".join(users.mapped("name")),
                        )
                    )
