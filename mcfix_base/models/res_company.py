# Copyright 2018 Creu Blanca
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, models


class Company(models.Model):
    _inherit = 'res.company'

    @api.model
    def create(self, vals):
        """ We need this method in order avoid the system to set the company
        by default on a new partner."""
        company = super(Company, self.with_context(company_id=False)).create(
            vals)
        return company
