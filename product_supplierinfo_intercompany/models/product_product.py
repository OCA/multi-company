# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.tools.safe_eval import safe_eval


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "product.intercompany.supplier.mixin"]

    def _prepare_sellers(self, params=False):
        sellers = super()._prepare_sellers(params=params)
        # Always filter the seller using the security rule
        # For two reason :
        # when sudo is used (filtering is needed)
        # when we have a "broken" cache
        # (if you do self.sudo().seller_ids then in the cache you have all
        # the seller even if you read it with self.seller_ids after)
        # so we need to filter
        rule = self.env.ref(
            "product_supplierinfo_intercompany.product_supplierinfo_intercomp_rule"
        ).sudo()
        domain = safe_eval(rule.domain_force, rule._eval_context())
        # use sudo to evaluate the access rule as we may not have the access
        # rigth when evaluating the field intercompany_pricelist_id.company_id
        seller_ids = sellers.sudo().filtered_domain(domain).ids
        return sellers.browse(seller_ids)

    def _get_intercompany_supplier_info_domain(self, pricelist):
        return [
            ("intercompany_pricelist_id", "=", pricelist.id),
            ("product_id", "=", self.id),
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
        ]

    def _prepare_intercompany_supplier_info(self, pricelist, min_qty):
        vals = super()._prepare_intercompany_supplier_info(pricelist, min_qty)
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
