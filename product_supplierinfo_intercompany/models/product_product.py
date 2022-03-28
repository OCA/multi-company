# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "product.intercompany.supplier.mixin"]

    def _get_intercompany_supplier_info_domain(self, pricelist):
        return [
            ("intercompany_pricelist_id", "=", pricelist.id),
            ("product_id", "=", self.id),
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
        ]

    def _prepare_intercompany_supplier_info(self, pricelist):
        vals = super()._prepare_intercompany_supplier_info(pricelist)
        vals.update(
            {
                "product_id": self.id,
                "product_tmpl_id": self.product_tmpl_id.id,
            }
        )
        return vals

    def _has_intercompany_price(self, pricelist):
        self.ensure_one()
        if (
            self.env["product.pricelist.item"].search(
                [
                    ("pricelist_id", "=", pricelist.id),
                    ("product_id", "=", self.id),
                ]
            )
            and pricelist.is_intercompany_supplier
        ):
            return True

    @api.depends("product_tmpl_id.pricelist_item_ids.fixed_price")
    def _compute_product_price(self):
        """We need the 'depends' in order to get the correct, updated price
        calculations when a pricelist item is added"""
        return super()._compute_product_price()
