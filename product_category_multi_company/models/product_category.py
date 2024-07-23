# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = ["multi.company.abstract", "product.category"]
    _name = "product.category"
    _description = "Product Category (Multi-Company)"

    @api.constrains("company_ids")
    def _check_product_companies_in_category(self):
        for category in self:
            if not category.company_ids:
                continue
            products = (
                self.env["product.template"]
                .sudo()
                .search([("categ_id", "=", category.id)])
            )
            for product in products:
                product_company_ids = product.company_ids
                if not all(
                    company in category.company_ids for company in product_company_ids
                ):
                    raise ValidationError(
                        _(
                            "The category's companies cannot be changed because some products "
                            "have companies not in the new set of category companies."
                        )
                    )

    @api.constrains("parent_id", "company_ids")
    def check_company_restriction(self):
        for record in self:
            parent_company_ids = record.parent_id.company_ids
            record_company_ids = record.company_ids

            if parent_company_ids and not all(
                company_id in parent_company_ids for company_id in record_company_ids
            ):
                raise ValidationError(
                    _(
                        "The parent category %(parent)s and your category %(child)s "
                        "must share the same companies."
                    )
                    % {"parent": record.parent_id.name, "child": record.name}
                )

            for child in record.child_id:
                child_company_ids = child.company_ids
                if record_company_ids and not all(
                    company_id in record_company_ids for company_id in child_company_ids
                ):
                    if child_company_ids:
                        msg = _(
                            "The category %(parent)s must be shared as the "
                            "child %(child)s belongs to companies %(companies)s."
                        ) % {
                            "parent": record.name,
                            "child": child.name,
                            "companies": ", ".join(child_company_ids.mapped("name")),
                        }
                    else:
                        msg = _(
                            "The category %(parent)s must be shared as the "
                            "child %(child)s is shared."
                        ) % {"parent": record.name, "child": child.name}
                    raise ValidationError(msg)
