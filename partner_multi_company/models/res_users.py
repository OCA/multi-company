# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html.html

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals):
        res = super(ResUsers, self).create(vals)
        if "company_ids" in vals:
            res.partner_id.company_ids = vals["company_ids"]
        return res

    def write(self, vals):
        res = super(ResUsers, self.with_context(from_res_users=True)).write(vals)
        if "company_ids" in vals:
            for user in self.sudo():
                new_company_ids = []
                company_ids_data = vals["company_ids"]
                if isinstance(company_ids_data, list) and user.partner_id.company_ids:
                    for item in company_ids_data:
                        if isinstance(item, tuple):
                            if item[0] == 4:
                                new_company_ids.append(item[1])
                            elif item[0] == 6:
                                new_company_ids.extend(item[2])
                        elif isinstance(item, list):
                            new_company_ids = item[2]
                        else:
                            new_company_ids.append(item)
                    user.partner_id.company_ids = [
                        (4, company_id) for company_id in new_company_ids
                    ]
        if "company_id" in vals:
            for user in self.sudo():
                if user.partner_id.company_ids:
                    user.partner_id.company_ids = [(4, vals["company_id"])]
        return res
