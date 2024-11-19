from odoo import Command, api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        for company in companies:
            for user in company.user_ids:
                if company not in user.partner_id.company_ids:
                    user.partner_id.company_ids = [Command.link(company.id)]
        return companies

    def write(self, vals):
        res = super().write(vals)
        if "user_ids" in vals:
            for company in self.sudo():
                for user in company.user_ids:
                    if company not in user.partner_id.company_ids:
                        user.partner_id.company_ids = [Command.link(company.id)]
        return res
