#  Copyright (c) Akretion 2021
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    quick_intercompany_stock_level = fields.Float(
        "Free quantity",
        compute="_compute_quick_intercompany_stock_level",
        search="_search_quick_intercompany_stock_level",
    )

    def _quick_intercompany_stock_level_field(self):
        return "qty_available"

    @api.depends("quick_uom_id")
    @api.depends_context("parent_id", "parent_model", "user")
    def _compute_quick_intercompany_stock_level(self):
        for rec in self:
            result = 0.0
            if self.env.context.get(
                "parent_model"
            ) == "purchase.order" and self.env.context.get("show_intercompany_qty"):
                purchase = self.env["purchase.order"].browse(
                    self.env.context.get("parent_id")
                )
                result = self._get_stock_level(rec, purchase)
            rec.quick_intercompany_stock_level = result

    def _get_seller_company(self, purchase):
        seller_partner = purchase.partner_id.commercial_partner_id
        return (
            self.env["res.company"]
            .sudo()
            .search([("partner_id", "=", seller_partner.id)])
        )

    def _get_warehouses(self, seller_company):
        return (
            self.env["stock.warehouse"]
            .sudo()
            .search([("company_id", "=", seller_company.id)])
        )

    def _get_stock_level(self, rec, purchase):
        seller_company = self._get_seller_company(purchase)
        if purchase and seller_company:
            warehouses = self._get_warehouses(seller_company)
            qty_raw = getattr(
                rec.sudo().with_context({"warehouse": warehouses.ids}),
                self._quick_intercompany_stock_level_field(),
            )
            return rec.uom_id._compute_quantity(qty_raw, rec.quick_uom_id)

    @api.model
    def _search_quick_intercompany_stock_level(self, operator, value):
        purchase = self.env["purchase.order"].browse(self.env.context.get("parent_id"))
        seller_company = self._get_seller_company(purchase)
        if purchase and seller_company:
            warehouses = self._get_warehouses(seller_company)
            product_ids = (
                self.sudo()
                .with_context({"warehouse": warehouses.ids})
                ._search_qty_available_new(operator, value)
            )
            return [("id", "in", product_ids)]
        return []

    def _default_quick_uom_id(self):
        if self.pma_parent.partner_id.origin_company_id and self.uom_intercompany_id:
            return self.uom_intercompany_id
        else:
            return super()._default_quick_uom_id()
