from odoo import _, models
from odoo.exceptions import Warning as UserError


class ProductIntercompanySupplierMixin(models.AbstractModel):
    _inherit = "product.intercompany.supplier.mixin"

    def _synchronise_supplier_info(self, pricelists=None):
        # replaced to add company_ids condition
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
                if (
                    record._has_intercompany_price(pricelist)
                    and record.sale_ok
                    and record.purchase_ok
                    and (
                        (
                            pricelist.company_id.id in record.company_ids.ids
                            and record.company_id.id in record.company_ids.ids
                        )
                        or (len(record.company_ids) == 0)
                    )
                ):
                    vals = record._prepare_intercompany_supplier_info(pricelist)
                    if supplierinfo:
                        supplierinfo.write(vals)
                    else:
                        supplierinfo.create(vals)
                elif supplierinfo:
                    supplierinfo.sudo().unlink()
                if (
                    record._has_intercompany_price(pricelist)
                    and pricelist.company_id.id in record.company_ids.ids
                    and record.company_id.id == pricelist.company_id.id
                ):
                    supplierinfo.sudo().unlink()
