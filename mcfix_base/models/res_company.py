from odoo import api, models


class Company(models.Model):
    _inherit = 'res.company'

    @api.model
    def create(self, vals):
        """ We need this method in order avoid the system to set the company
        by default on a new partner. Because """
        company = super(Company, self.with_context(company_id=False)).create(
            vals)
        return company
