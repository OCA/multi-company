# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = ["multi.company.abstract", "product.product"]
    _name = "product.product"
    _description = "Product Variant (Multi-Company)"

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
