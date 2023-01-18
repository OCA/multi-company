# Copyright (C) 2023-Today: GRAP (<http://www.grap.coop/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _configure_favorite_product_category(self):
        for company in self:
            categories = self.env["product.category"].sudo().with_context(
                force_company=company.id
            ).search([("parent_id", "=", False)])
            categories.write({"is_favorite": True})

    @api.model
    def create(self, vals):
        company = super().create(vals)
        company._configure_favorite_product_category()
        return company
