# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "product.intercompany.supplier.mixin"]

    pricelist_item_ids = fields.One2many("product.pricelist.item", "product_tmpl_id")

    def _get_intercompany_supplier_info_domain(self, pricelist):
        return [
            ("intercompany_pricelist_id", "=", pricelist.id),
            ("product_id", "=", False),
            ("product_tmpl_id", "=", self.id),
        ]

    def _prepare_intercompany_supplier_info(self, pricelist):
        vals = super()._prepare_intercompany_supplier_info(pricelist)
        vals["product_tmpl_id"] = self.id
        return vals

    def _has_intercompany_price(self, pricelist):
        self.ensure_one()
        if self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", pricelist.id),
                ("product_tmpl_id", "=", self.id),
                ("product_id", "=", False),
            ]
        ):
            return True
        if self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", pricelist.id),
                ("applied_on", "=", "2_product_category"),
                ("product_tmpl_id", "=", False),
                ("product_id", "=", False),
            ]
        ):
            return True
        if self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", pricelist.id),
                ("applied_on", "=", "3_global"),
                ("product_tmpl_id", "=", False),
                ("product_id", "=", False),
            ]
        ):
            return True

    @api.depends("pricelist_item_ids.fixed_price")
    def _compute_template_price(self):
        """We need the 'depends' in ordder to get the correct, updated price
        calculations when a pricelist item is added"""
        return super()._compute_template_price()
