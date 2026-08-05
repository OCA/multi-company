# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    supplier_stock_info = fields.Html(
        string="Supplier Stock",
        compute="_compute_supplier_stock_info",
    )

    @api.depends("product_id", "order_id.partner_id")
    def _compute_supplier_stock_info(self):
        stock_field = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "sale_order_line_stock_info.stock_field_on_sol", "qty_available"
            )
        )
        for line in self:
            info = ""
            product = line.product_id
            partner = line.order_id.partner_id
            if product and partner:
                vendor_company = (
                    self.env["res.company"]
                    .sudo()
                    .search(
                        [("partner_id", "=", partner.commercial_partner_id.id)],
                        limit=1,
                    )
                )
                if vendor_company:
                    warehouses = (
                        self.env["stock.warehouse"]
                        .sudo()
                        .search(
                            [
                                ("company_id", "=", vendor_company.id),
                                ("display_stock_on_sol", "=", True),
                            ]
                        )
                    )
                    if warehouses:
                        total = 0.0
                        for warehouse in warehouses:
                            total += product.sudo().with_context(
                                warehouse=warehouse.id,
                                force_company=vendor_company.id,
                            )[stock_field]
                        info = f"<span>{total}</span>"
            line.supplier_stock_info = info
