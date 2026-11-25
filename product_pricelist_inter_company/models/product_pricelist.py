# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain

_SKIP_SYNC = "product_pricelist_inter_company_skip_sync"


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    purchase_company_ids = fields.Many2many(
        comodel_name="res.company",
        relation="product_pricelist_inter_company_purchase_company_rel",
        column1="pricelist_id",
        column2="company_id",
        string="Purchasing Companies",
        copy=False,
        help="Companies that purchase from this pricelist's Company. "
        "Vendor supplierinfo records are automatically maintained for these companies.",
    )

    @api.constrains("purchase_company_ids", "company_id")
    def _constrains_purchase_companies_require_vendor_company(self):
        for pricelist in self:
            if pricelist.purchase_company_ids and not pricelist.company_id:
                raise ValidationError(
                    self.env._(
                        "Purchasing companies can only be set on a pricelist "
                        "that belongs to a specific vendor company."
                    )
                )

    def write(self, vals):
        if "company_id" in vals and self.filtered("purchase_company_ids"):
            raise UserError(
                self.env._(
                    "Cannot change the vendor company on a pricelist that has "
                    "purchasing companies configured. Remove the purchasing "
                    "companies first — this will also remove the associated vendor "
                    "price entries."
                )
            )
        old_purchase_companies = {
            pricelist.id: pricelist.purchase_company_ids for pricelist in self
        }
        result = super().write(vals)
        if "purchase_company_ids" in vals and not self.env.context.get(_SKIP_SYNC):
            self._sync_supplierinfo_on_purchase_company_change(old_purchase_companies)
        return result

    def _sync_supplierinfo_on_purchase_company_change(self, old_purchase_companies):
        for pricelist in self:
            old_companies = old_purchase_companies[pricelist.id]
            added = pricelist.purchase_company_ids - old_companies
            removed = old_companies - pricelist.purchase_company_ids
            if added:
                pricelist._create_supplierinfo_for_companies(added)
            if removed:
                pricelist._delete_supplierinfo_for_companies(removed)

    def _create_supplierinfo_for_companies(self, companies):
        self.ensure_one()
        if not self.company_id:
            return
        SupplierInfo = (
            self.env["product.supplierinfo"].sudo().with_context(**{_SKIP_SYNC: True})
        )
        product_items = self.item_ids.filtered(
            lambda pricelist_item: (
                pricelist_item.applied_on in ("1_product", "0_product_variant")
            )
        )
        existing_supinfos = SupplierInfo.search(
            Domain("pricelist_item_id", "in", product_items.ids)
            & Domain("company_id", "in", companies.ids)
        )
        existing_keys = {
            (supinfo.pricelist_item_id.id, supinfo.company_id.id)
            for supinfo in existing_supinfos
        }
        vals_list = []
        for item in product_items:
            for company in companies:
                if (item.id, company.id) not in existing_keys:
                    vals_list.append(item._build_supplierinfo_vals(company))
        if vals_list:
            SupplierInfo.create(vals_list)

    def _delete_supplierinfo_for_companies(self, companies):
        self.ensure_one()
        self.env["product.supplierinfo"].sudo().with_context(
            **{_SKIP_SYNC: True}
        ).search(
            Domain("pricelist_item_id", "in", self.item_ids.ids)
            & Domain("company_id", "in", companies.ids)
        ).unlink()
