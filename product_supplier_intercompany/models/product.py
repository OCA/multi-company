# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError


class ProductIntercompanySupplierMixin(models.AbstractModel):
    _name = "product.intercompany.supplier.mixin"
    _description = "Intercompany product mixin"

    def _has_intercompany_price(self, pricelist):
        raise NotImplementedError

    def _get_intercompany_supplier_info_domain(self, pricelist):
        raise NotImplementedError

    def _prepare_intercompany_supplier_info(self, pricelist):
        self.ensure_one()
        price = self.uom_id._compute_price(self.price, self.uom_po_id)
        res = {
            "intercompany_pricelist_id": pricelist.id,
            "name": pricelist.company_id.partner_id.id,
            "company_id": False,
            "price": price,
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
            for record in self.with_context(
                pricelist=pricelist.id, automatic_intercompany_sync=True
            ):
                domain = record._get_intercompany_supplier_info_domain(pricelist)
                supplierinfo = record.env["product.supplierinfo"].sudo().search(domain)
                if record._has_intercompany_price(pricelist):
                    vals = record._prepare_intercompany_supplier_info(pricelist)
                    if supplierinfo:
                        supplierinfo.write(vals)
                    else:
                        supplierinfo.create(vals)
                elif supplierinfo:
                    supplierinfo.sudo().unlink()


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
        vals = super(ProductProduct, self)._prepare_intercompany_supplier_info(
            pricelist
        )
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
        """We need the 'depends' in ordder to get the correct, updated price
        calculations when a pricelist item is added"""
        res = super(ProductProduct, self)._compute_product_price()
        return res


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
        vals = super(ProductTemplate, self)._prepare_intercompany_supplier_info(
            pricelist
        )
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

    @api.depends("pricelist_item_ids.fixed_price")
    def _compute_template_price(self):
        """We need the 'depends' in ordder to get the correct, updated price
        calculations when a pricelist item is added"""
        res = super(ProductTemplate, self)._compute_template_price()
        return res


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    intercompany_pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        inverse_name="generated_supplier_info_ids",
    )

    pricelist_item_id = fields.Many2one(comodel_name="product.pricelist.item")

    def _check_intercompany_supplier(self):
        if not self._context.get("automatic_intercompany_sync"):
            for record in self:
                if record.mapped("intercompany_pricelist_id"):
                    raise UserError(
                        _(
                            "This supplier info can not be edited as it's "
                            "linked to an intercompany 'sale' pricelist.\n "
                            "Please modify the information on the 'sale' "
                            "pricelist"
                        )
                    )

    def write(self, vals):
        self._check_intercompany_supplier()
        return super(ProductSupplierinfo, self).write(vals)

    @api.model
    def create(self, vals):
        record = super(ProductSupplierinfo, self).create(vals)
        record._check_intercompany_supplier()
        return record

    def unlink(self):
        self._check_intercompany_supplier()
        return super(ProductSupplierinfo, self).unlink()
