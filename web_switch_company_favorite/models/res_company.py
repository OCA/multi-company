# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# @author Pierre Verkest <pierre@verkest.fr>
from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def get_companies_from_filter(self, filter_id):
        company_filter = self.env["ir.filters"].browse(filter_id).exists()
        if not company_filter or company_filter.model_id != "res.company":
            return []
        domain = company_filter._get_eval_domain()
        allowed_company_ids = self.env.user.company_ids.ids
        search_domain = [("id", "in", allowed_company_ids), *domain]
        matching_companies = self.env["res.company"].sudo().search(search_domain)
        return matching_companies.ids
