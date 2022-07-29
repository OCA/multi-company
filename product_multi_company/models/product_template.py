# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class ProductTemplate(models.Model):
    _inherit = ["multi.company.abstract", "product.template"]
    _name = "product.template"
    _description = "Product Template (Multi-Company)"

    def recompute_no_company_ids(self):
        '''
            Cron job
            Recomputed no_company_ids for existing product template record
        '''
        products = self.env['product.template'].search([])
        for product in products:
            if product.company_ids:
                product.no_company_ids = False
