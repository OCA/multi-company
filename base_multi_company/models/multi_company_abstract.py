# -*- coding: utf-8 -*-
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
        default=lambda s: s._default_company_ids(),
        auto_join=True,
    )

    @api.model
    def _default_company_ids(self):
        Companies = self.env['res.company']
        return [
            (6, 0, Companies._company_default_get().ids),
        ]

    @api.multi
    def _compute_company_id(self):
        user_company = self.env.user.company_id
        for record in self:
            # Give the priority of the current company of the user to avoid
            # access right error
            if user_company.id in record.company_ids.ids:
                record.company_id = user_company.id
                continue
            for company in record.company_ids:
                if company.id in self.env.user.company_ids.ids:
                    record.company_id = company.id
                    break

    @api.multi
    def _inverse_company_id(self):
        for record in self:
            if record.company_id and record.company_id.id not in \
                    record.company_ids.ids:
                record.company_ids = [(4, record.company_id.id)]

    @api.model
    def _search_company_id(self, operator, value):
        return [('company_ids', operator, value)]
