# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.onchange("company_id")
    def onchange_company_id(self):
        self._sync_parent_company()

    def _sync_parent_company(self):
        partner_companies = self.env["res.company"].sudo().search([]).partner_id
        for record in self:
            # Note if we manually affect a user to a company (res.partner)
            # that is not an address of a company (res.company)
            # it's maybe an "external" user that do not belong to a specific company
            # So we do not update in this case
            # For example, you can have Akretion user attached to the res.partner
            # Akretion, and this partner is not an address of a company
            if not record.parent_id or record.parent_id in partner_companies:
                record.parent_id = record.company_id.partner_id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_parent_company()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "company_id" in vals:
            self._sync_parent_company()
        return res
