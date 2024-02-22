from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    company_map_id = fields.Many2one("account.tax.company.map")

    @api.constrains("company_map_id")
    def _check_company_map_id(self):
        for tax in self:
            company_map_id = tax.company_map_id
            if company_map_id:
                company_map_id._check_tax_ids()
