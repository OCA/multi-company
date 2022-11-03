# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class CompanyCheckMixin(models.AbstractModel):
    _name = "company.check.mixin"
    _description = "Base Company Check Mixin"

    def _get_incompatible_companies(self, companies):

        return companies - self.company_id

    def _allowed_company_get_fields_to_check(self):
        return []

    @api.constrains("company_id")
    def allowed_company(self):
        for record in self.sudo():
            if not record.company_id:
                continue
            for field in self._allowed_company_get_fields_to_check():
                incompatible_companies = record._get_incompatible_companies(
                    record[field].company_id
                )
                if incompatible_companies:
                    incompatible_companies_name = ", ".join(
                        incompatible_companies.mapped("name")
                    )
                    raise UserError(
                        _(
                            f"It's not possible to set the company "
                            f"{record.company_id.name} to the record "
                            f"{record.name} as it have been used by "
                            f"{incompatible_companies_name}"
                        )
                    )
