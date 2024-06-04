# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class ProductIntercompanySupplierMixin(models.AbstractModel):
    _name = "product.intercompany.supplier.mixin"
    _description = "Intercompany product mixin"

    def _has_intercompany_price(self, pricelist):
        raise NotImplementedError

    def _get_intercompany_supplier_info_domain(self, pricelist):
        raise NotImplementedError

    def _prepare_intercompany_supplier_info(self, pricelist, min_qty):
        self.ensure_one()
        price = pricelist._get_product_price(self, min_qty, self.uom_po_id)
        res = {
            "intercompany_pricelist_id": pricelist.id,
            "partner_id": pricelist.company_id.partner_id.id,
            "company_id": False,
            "min_qty": min_qty,
            "price": price,
        }
        return res

    def _update_or_create_supplierinfo(self, supplierinfos, pricelist):
        supplierinfos = supplierinfos.with_context(automatic_intercompany_sync=True)
        today = fields.Date.today()
        items = pricelist._get_applicable_rules(self, today)
        if self._name == "product.template":
            items = items.filtered(lambda r: not r.product_id)
        elif self._name == "product.product":
            items = items.filtered(lambda r: r.product_id == self)
        for item in items:
            vals = self._prepare_intercompany_supplier_info(
                pricelist, item.min_quantity
            )
            supplierinfo = supplierinfos.filtered(
                lambda r: r.min_qty == item.min_quantity
            )
            if supplierinfo:
                supplierinfo.write(vals)
            else:
                supplierinfos.create(vals)
        for supplierinfo in supplierinfos:
            item = items.filtered(lambda r: r.min_quantity == supplierinfo.min_qty)
            if not item:
                supplierinfo.unlink()

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
            for record in self.sudo().with_context(automatic_intercompany_sync=True):
                domain = record._get_intercompany_supplier_info_domain(pricelist)
                supplierinfos = record.env["product.supplierinfo"].search(domain)
                if (
                    record._has_intercompany_price(pricelist)
                    and record.sale_ok
                    and record.purchase_ok
                ):
                    record._update_or_create_supplierinfo(supplierinfos, pricelist)
                elif supplierinfos:
                    supplierinfos.sudo().unlink()
