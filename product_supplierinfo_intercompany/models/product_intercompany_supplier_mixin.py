# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import UserError


class ProductIntercompanySupplierMixin(models.AbstractModel):
    _name = "product.intercompany.supplier.mixin"
    _description = "Intercompany product mixin"

    def _has_intercompany_price(self, pricelist):
        raise NotImplementedError

    def _get_intercompany_supplier_info_domain(self, pricelist):
        raise NotImplementedError

    def _prepare_intercompany_supplier_info(self, pricelist):
        self.ensure_one()
        price = pricelist._get_product_price(self, 0, self.uom_po_id)
        res = {
            "intercompany_pricelist_id": pricelist.id,
            "partner_id": pricelist.company_id.partner_id.id,
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
            for record in self.sudo().with_context(automatic_intercompany_sync=True):
                domain = record._get_intercompany_supplier_info_domain(pricelist)
                supplierinfo = record.env["product.supplierinfo"].search(domain)
                if (
                    record._has_intercompany_price(pricelist)
                    and record.sale_ok
                    and record.purchase_ok
                ):
                    vals = record._prepare_intercompany_supplier_info(pricelist)
                    if supplierinfo:
                        supplierinfo.write(vals)
                    else:
                        supplierinfo.create(vals)
                elif supplierinfo:
                    supplierinfo.sudo().unlink()
