# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductPackaging(models.Model):
    _inherit = ["multi.company.abstract", "product.packaging"]
    _name = "product.packaging"
    _description = "Product Packaging (Multi-Company)"

    @api.constrains("package_type_id", "company_ids")
    def _check_package_type_company(self):
        for packaging in self:
            if packaging.package_type_id and packaging.company_ids:
                allowed_companies = packaging.package_type_id.company_ids
                if not (packaging.company_ids & allowed_companies):
                    raise ValidationError(
                        _(
                            "The selected package type is not available for the "
                            "companies assigned to this packaging.\n\n"
                            "Package type companies: %(pt_companies)s\n"
                            "Packaging companies: %(p_companies)s"
                        )
                        % {
                            "pt_companies": ", ".join(allowed_companies.mapped("name")),
                            "p_companies": ", ".join(
                                packaging.company_ids.mapped("name")
                            ),
                        }
                    )
