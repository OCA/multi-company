#  Copyright (c) Akretion 2021
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    quick_stock_level = fields.Char(
        "Free quantity", compute="_compute_quick_stock_level"
    )

    def _quick_stock_level_field(self):
        return "qty_available"

    @api.depends("quick_uom_id")
    @api.depends_context("parent_id", "parent_model", "user")
    def _compute_quick_stock_level(self):
        for rec in self:
            result = "N/A"
            if self.env.context.get("parent_model") == "purchase.order":
                purchase = self.env["purchase.order"].browse(
                    self.env.context.get("parent_id")
                )
                seller_partner = purchase.partner_id.commercial_partner_id
                seller_company = (
                    self.env["res.company"]
                    .sudo()
                    .search([("partner_id", "=", seller_partner.id)])
                )
                if purchase and seller_company:
                    warehouse_ids = (
                        self.env["stock.warehouse"]
                        .sudo()
                        .search([("company_id", "=", seller_company.id)])
                        .ids
                    )
                    qty_raw = getattr(
                        rec.sudo().with_context({"warehouse": warehouse_ids}),
                        self._quick_stock_level_field(),
                    )
                    result = rec.uom_id._compute_quantity(qty_raw, rec.quick_uom_id)
            rec.quick_stock_level = result

    def _default_quick_uom_id(self):
        if self.pma_parent.partner_id.origin_company_id and self.uom_intercompany_id:
            return self.uom_intercompany_id
        else:
            return super()._default_quick_uom_id()
