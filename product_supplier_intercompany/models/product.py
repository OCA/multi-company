# coding: utf-8
# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models, fields
from odoo.exceptions import Warning as UserError


class ProductIntercompanySupplierMixin(models.AbstractModel):
    _name = "product.intercompany.supplier.mixin"

    def _has_intercompany_price(self, pricelist):
        raise NotImplementedError

    def _get_intercompany_supplier_info_domain(self, pricelist):
        raise NotImplementedError

    @api.multi
    def _prepare_intercompany_supplier_info(self, pricelist):
        quantities = [1] * len(self)  # quantity of 1 for each product
        partners = [pricelist.company_id.partner_id] * len(self)
        prices = pricelist.get_products_price(self, quantities, partners)
        res = {}
        for product in self:
            res[product.id] = {
                "intercompany_pricelist_id": pricelist.id,
                "name": pricelist.company_id.partner_id.id,
                "company_id": False,
                "price": prices.get(product.id) or 0,
                "min_qty": 1,
            }
        return res

    def _synchronise_supplier_info(self, pricelists=None):
        if not pricelists:
            pricelists = self.env["product.pricelist"].search(
                [("is_intercompany_supplier", "=", True)]
            )
        for pricelist in pricelists:
            if not pricelist.is_intercompany_supplier:
                raise UserError(
                    _("The pricelist %s is not intercompany") % pricelist.name
                )
            # We pass the pricelist in the context in order to get the right
            # sale price on record.price (compatible v8 to v12)
            self = self.with_context(
                pricelist=pricelist.id, automatic_intercompany_sync=True
            )
            products_vals = self._prepare_intercompany_supplier_info(pricelist)
            for product in self:
                vals = products_vals.get(product.id)
                domain = product._get_intercompany_supplier_info_domain(
                    pricelist
                )
                supplier = (
                    product.env["product.supplierinfo"].sudo().search(domain)
                )
                if vals and product._has_intercompany_price(pricelist):
                    if supplier:
                        supplier.write(vals)
                    else:
                        supplier.create(vals)
                elif supplier:
                    supplier.sudo().unlink()


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "product.intercompany.supplier.mixin"]

    def _get_intercompany_supplier_info_domain(self, pricelist):
        return [
            ("intercompany_pricelist_id", "=", pricelist.id),
            ("product_id", "=", self.id),
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
        ]

    @api.multi
    def _prepare_intercompany_supplier_info(self, pricelist):
        res = super(ProductProduct, self)._prepare_intercompany_supplier_info(
            pricelist
        )
        for product_id, vals in res.items():
            vals.update(
                {
                    "product_id": product_id,
                    "product_tmpl_id": self.browse(
                        product_id
                    ).product_tmpl_id.id,
                }
            )
        return res

    def _has_intercompany_price(self, pricelist):
        self.ensure_one()
        if self.env["product.pricelist.item"].search(
            [("pricelist_id", "=", pricelist.id), ("product_id", "=", self.id)]
        ):
            return True


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "product.intercompany.supplier.mixin"]

    def _get_intercompany_supplier_info_domain(self, pricelist):
        return [
            ("intercompany_pricelist_id", "=", pricelist.id),
            ("product_id", "=", False),
            ("product_tmpl_id", "=", self.id),
        ]

    def _prepare_intercompany_supplier_info(self, pricelist):
        res = super(ProductTemplate, self)._prepare_intercompany_supplier_info(
            pricelist
        )
        for product_id, vals in res.items():
            vals["product_tmpl_id"] = product_id
        return res

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


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    intercompany_pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        inverse_name="generated_supplier_info_ids",
    )

    def _check_intercompany_supplier(self):
        if not self._context.get("automatic_intercompany_sync"):
            for record in self:
                if record.mapped("intercompany_pricelist_id"):
                    raise UserError(
                        _(
                            "This supplier info can't be edited as it's linked"
                            " to an intercompany 'sale' pricelist.\n Please "
                            "modify the information on the 'sale' pricelist"
                        )
                    )

    @api.multi
    def write(self, vals):
        self._check_intercompany_supplier()
        return super(ProductSupplierinfo, self).write(vals)

    @api.model
    def create(self, vals):
        record = super(ProductSupplierinfo, self).create(vals)
        record._check_intercompany_supplier()
        return record

    @api.multi
    def unlink(self):
        self._check_intercompany_supplier()
        return super(ProductSupplierinfo, self).unlink()
