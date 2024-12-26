# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    _order = "code,name"

    code = fields.Char()

    _sql_constraints = [
        ("code_uniq", "unique (code)", "The company code must be unique !")
    ]

    @api.depends("code", "name")
    def _compute_display_name(self):
        for company in self:
            if not company.code:
                company.display_name = company.name
            else:
                company.display_name = f"{company.code} - {company.name}"

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", operator, name), ("name", operator, name)]
        company = self.search(domain + args, limit=limit)
        return [(record.id, record.display_name) for record in company]
