# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    _order = 'code, name'

    code = fields.Char(string='Code')

    complete_name = fields.Char(
        string='Complete Name', compute='_compute_complete_name', store=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The company code must be unique !')
    ]

    @api.depends('code', 'name')
    def _compute_complete_name(self):
        for company in self:
            if not company.code:
                company.complete_name = company.name
            else:
                company.complete_name = "%s - %s" % (
                    company.code, company.name)
