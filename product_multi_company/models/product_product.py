# Copyright 2020 Kevin Graveman <k.graveman@onestein.nl>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = ["multi.company.abstract", "product.product"]
    _name = "product.product"
    _description = "Product Variant (Multi-Company)"

    company_ids = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
        default=lambda self: self._default_company_ids(),
    )

    @api.model
    def create(self, values):
        """Ensure the template initially has the same companies as the variant."""
        if not values.get("company_ids") and values.get("product_tmpl_id"):
            values["company_ids"] = [
                (
                    6,
                    0,
                    self.env["product.template"]
                    .browse(values.get("product_tmpl_id"))
                    .company_ids.ids,
                )
            ]
        res = super(ProductProduct, self).create(values)
        res.product_tmpl_id.write({"company_ids": [(6, 0, res.company_ids.ids)]})
        return res

    def write(self, values):
        """Ensure the template's companies are a superset of the variant's."""
        if self.env.context.get("company_inverse"):
            return super(ProductProduct, self).write(values)
        if values.get("company_ids") and values["company_ids"][0][0] == 6:
            # Add companies to the template, but don't remove them.
            companies_to_add = list(
                set(values.get("company_ids")[0][2]).difference(self.company_ids.ids)
            )
            companies_to_add.extend(self.product_tmpl_id.company_ids.ids)
            if companies_to_add:
                self.product_tmpl_id.write({"company_ids": [(6, 0, companies_to_add)]})
        return super(ProductProduct, self).write(values)
