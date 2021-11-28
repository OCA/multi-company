# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    foo_company_dependent_field = fields.Char(company_dependent=True)

    @api.model
    def _commercial_fields(self):
        self.check_access_rule("write")
        return super()._commercial_fields() + ["foo_company_dependent_field"]
