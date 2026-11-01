# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .product_pricelist import _SKIP_SYNC

PRICE_FIELDS = frozenset(
    {
        "fixed_price",
        "percent_price",
        "price_discount",
        "price_surcharge",
        "price_round",
        "price_markup",
        "price_min_margin",
        "price_max_margin",
        "compute_price",
        "base",
        "base_pricelist_id",
    }
)

STRUCTURAL_FIELDS = frozenset({"applied_on", "product_tmpl_id", "product_id"})


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    supplierinfo_ids = fields.One2many(
        comodel_name="product.supplierinfo",
        inverse_name="pricelist_item_id",
        string="Vendor Prices",
    )

    @api.model_create_multi
    def create(self, vals_list):
        items = super().create(vals_list)
        if not self.env.context.get(_SKIP_SYNC):
            items._sync_supplierinfo_on_create()
        return items

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get(_SKIP_SYNC):
            self._sync_supplierinfo_on_write(vals)
        return result

    def unlink(self):
        if not self.env.context.get(_SKIP_SYNC):
            self._delete_managed_supplierinfos()
        return super().unlink()

    # --- sync helpers ---

    def _get_sync_price(self):
        self.ensure_one()
        if self.compute_price == "fixed":
            return self.fixed_price, self.currency_id.id
        product = self.product_id or self.product_tmpl_id.product_variant_id
        if not product:
            return 0.0, self.currency_id.id
        price = self._compute_price(
            product,
            quantity=1.0,
            uom=product.uom_id,
            date=fields.Datetime.now(),
            currency=self.currency_id,
        )
        return price, self.currency_id.id

    def _build_supplierinfo_vals(self, company):
        self.ensure_one()
        price, currency_id = self._get_sync_price()
        vals = {
            "partner_id": self.pricelist_id.company_id.partner_id.id,
            "company_id": company.id,
            "pricelist_item_id": self.id,
            "price": price,
            "currency_id": currency_id,
        }
        if self.applied_on == "1_product":
            vals["product_tmpl_id"] = self.product_tmpl_id.id
        else:
            # supplierinfo._sanitize_vals() fills product_tmpl_id from product_id
            vals["product_id"] = self.product_id.id
        return vals

    def _filter_supplierinfo_pricelist_items(self):
        return self.filtered(
            lambda item: (
                item.applied_on in ("1_product", "0_product_variant")
                and item.pricelist_id
                and item.pricelist_id.company_id
                and item.pricelist_id.purchase_company_ids
            )
        )

    def _sync_supplierinfo_on_create(self):
        SupplierInfo = (
            self.env["product.supplierinfo"].sudo().with_context(**{_SKIP_SYNC: True})
        )
        vals_list = []
        for item in self._filter_supplierinfo_pricelist_items():
            for company in item.pricelist_id.purchase_company_ids:
                vals_list.append(item._build_supplierinfo_vals(company))
        if vals_list:
            SupplierInfo.create(vals_list)

    def _sync_supplierinfo_on_write(self, vals):
        if STRUCTURAL_FIELDS & vals.keys():
            self._sync_supplierinfo_structural_change()
        elif PRICE_FIELDS & vals.keys():
            self._sync_supplierinfo_price_update()

    def _sync_supplierinfo_price_update(self):
        for item in self._filter_supplierinfo_pricelist_items():
            supinfos = item.sudo().supplierinfo_ids
            if not supinfos:
                continue
            price, currency_id = item._get_sync_price()
            supinfos.with_context(**{_SKIP_SYNC: True}).write(
                {"price": price, "currency_id": currency_id}
            )

    def _sync_supplierinfo_structural_change(self):
        SupplierInfo = (
            self.env["product.supplierinfo"].sudo().with_context(**{_SKIP_SYNC: True})
        )
        now_eligible = self._filter_supplierinfo_pricelist_items()

        # Items no longer eligible → delete their supinfos
        for item in self - now_eligible:
            supinfos = item.sudo().supplierinfo_ids
            if supinfos:
                supinfos.with_context(**{_SKIP_SYNC: True}).unlink()

        # Items eligible now → update existing supinfos or create missing ones
        for item in now_eligible:
            price, currency_id = item._get_sync_price()
            if item.applied_on == "1_product":
                product_vals = {
                    "product_tmpl_id": item.product_tmpl_id.id,
                    "product_id": False,
                }
            else:
                product_vals = {"product_id": item.product_id.id}

            existing_by_company = {
                supinfo.company_id: supinfo for supinfo in item.sudo().supplierinfo_ids
            }
            purchase_companies = item.pricelist_id.purchase_company_ids
            to_create = []

            for company in purchase_companies:
                if company in existing_by_company:
                    existing_by_company[company].with_context(
                        **{_SKIP_SYNC: True}
                    ).write(
                        {**product_vals, "price": price, "currency_id": currency_id}
                    )
                else:
                    to_create.append(item._build_supplierinfo_vals(company))

            stale = item.sudo().supplierinfo_ids.filtered(
                lambda supinfo, pc=purchase_companies: supinfo.company_id not in pc
            )
            if stale:
                stale.with_context(**{_SKIP_SYNC: True}).unlink()

            if to_create:
                SupplierInfo.create(to_create)

    def _delete_managed_supplierinfos(self):
        supinfos = self.sudo().mapped("supplierinfo_ids")
        if supinfos:
            supinfos.with_context(**{_SKIP_SYNC: True}).unlink()
