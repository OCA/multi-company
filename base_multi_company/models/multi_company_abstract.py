# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class MultiCompanyAbstract(models.AbstractModel):

    _name = "multi.company.abstract"
    _description = "Multi-Company Abstract"

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        compute="_compute_company_id",
        search="_search_company_id",
    )
    company_ids = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
        default=lambda self: self._default_company_ids(),
    )

    def _default_company_ids(self):
        return self.browse(self.env.company.ids)

    @api.depends("company_ids")
    def _compute_company_id(self):
        current_companies = self.env.companies
        for record in self:
            if all(elem in record.company_ids.ids for elem in current_companies.ids):
                record.company_id = self.env.company.id
            else:
                record.company_id = record.company_ids[:1].id

    def _search_company_id(self, operator, value):
        return [("company_ids", operator, value)]
