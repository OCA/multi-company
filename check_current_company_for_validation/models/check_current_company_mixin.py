# Copyright 2024 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class CheckCurrentCompanyMixin(models.AbstractModel):
    _name = "check.current.company.mixin"
    _description = "Check Current Company Mixin"

    def check_current_company(self):
        if self.env.company != self.company_id:
            raise UserError(_("You can't validate a record from another company"))
        return True
