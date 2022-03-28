# © 2019 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import Warning as UserError


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
            for record in self.sudo().with_context(
                pricelist=pricelist.id, automatic_intercompany_sync=True
            ):
                domain = record._get_intercompany_supplier_info_domain(pricelist)
                supplierinfo = record.env["product.supplierinfo"].search(domain)
                if record._has_intercompany_price(pricelist):
                    vals = record._prepare_intercompany_supplier_info(pricelist)
                    if supplierinfo:
                        supplierinfo.write(vals)
                    else:
                        supplierinfo.create(vals)
                elif supplierinfo:
                    supplierinfo.sudo().unlink()
