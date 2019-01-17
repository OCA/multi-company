# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class MultiCompanyAbstract(models.AbstractModel):

    _name = 'multi.company.abstract'
    _description = 'Multi-Company Abstract'

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        compute='_compute_company_id',
        inverse='_inverse_company_id',
        search='_search_company_id',
    )
    company_ids = fields.Many2many(
        string='Companies',
        comodel_name='res.company.assignment',
        auto_join=True,
    )

    @api.depends('company_ids')
    def _compute_company_id(self):
        user_company = self.env.user.company_id
        for record in self:
            # Give the priority of the current company of the user to avoid
            # access right error
            if user_company.id in record.company_ids.ids:
                record.company_id = user_company.id
            else:
                record.company_id = record.company_ids[:1].id

    @api.multi
    def _inverse_company_id(self):
        for record in self:
            # Checking id not falsy due to bad data that can put '' in id
            if record.company_id.id:
                if record.company_id.id not in record.company_ids.ids:
                    record.company_ids = [(4, record.company_id.id)]
            else:
                # Empty the list of allowed companies (so it means all
                # companies are allowed) as it's the equivalent
                record.company_ids = [(5, )]

    @api.model
    def _search_company_id(self, operator, value):
        return [('company_ids', operator, value)]
