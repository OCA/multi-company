# Copyright (C) 2023-Today: GRAP (<http://www.grap.coop/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _configure_favorite_product_category(self):
        for company in self:
            categories = (
                self.env["product.category"]
                .sudo()
                .with_company(company)
                .search([("parent_id", "=", False)])
            )
            categories.write({"is_favorite": True})

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies._configure_favorite_product_category()
        return companies
