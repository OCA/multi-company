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

    def _prepare_intercompany_supplier_info(self, pricelist, min_qty):
        vals = super()._prepare_intercompany_supplier_info(pricelist, min_qty)
        vals["product_tmpl_id"] = self.id
        return vals

    def _has_intercompany_price(self, pricelist):
        self.ensure_one()

        def _get_all_categs(categ):
            if categ.parent_id:
                return categ | _get_all_categs(categ.parent_id)
            else:
                return categ

        domains = [
            [
                ("pricelist_id", "=", pricelist.id),
                ("product_tmpl_id", "=", self.id),
                ("product_id", "=", False),
            ],
            [
                ("pricelist_id", "=", pricelist.id),
                ("applied_on", "=", "2_product_category"),
                ("categ_id", "in", _get_all_categs(self.categ_id).ids),
                ("product_tmpl_id", "=", False),
                ("product_id", "=", False),
            ],
            [
                ("pricelist_id", "=", pricelist.id),
                ("applied_on", "=", "3_global"),
                ("product_tmpl_id", "=", False),
                ("product_id", "=", False),
            ],
        ]
        for domain in domains:
            item = self.env["product.pricelist.item"].search(domain)
            if item:
                return item

    @api.depends("pricelist_item_ids.fixed_price")
    def _compute_template_price(self):
        """We need the 'depends' in order to get the correct, updated price
        calculations when a pricelist item is added"""
        return super()._compute_template_price()

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        for rec in self:
            if rec.sale_ok and rec.purchase_ok:
                rec._synchronise_supplier_info()
        return res

    def write(self, vals):
        res = super().write(vals)
        if "sale_ok" in vals or "purchase_ok" in vals:
            for rec in self:
                rec._synchronise_supplier_info()
        return res
