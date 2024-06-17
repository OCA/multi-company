# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("company_ids", "categ_id")
    def _check_company_ids_in_category(self):
        for product in self:
            product_company_ids = product.company_ids
            category_company_ids = product.categ_id.company_ids
            if category_company_ids and not all(
                company in category_company_ids for company in product_company_ids
            ):
                raise ValidationError(
                    _(
                        "The product's companies must be a subset of the category's companies."
                    )
                )
