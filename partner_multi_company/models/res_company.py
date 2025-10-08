# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        # The new company is added to the user
        # but that does not trigger the user's write
        # that would align the partner's companies,
        # so we have to do it explicitly
        for company in companies:
            for user in company.user_ids:
                # If the partner has no companies,
                # it means it already accepts all the companies
                # so there is no need to add the new one
                if user.partner_id.company_ids:
                    user.partner_id.company_ids += company
        return companies
