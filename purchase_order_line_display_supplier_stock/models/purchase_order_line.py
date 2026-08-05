# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    supplier_stock_info = fields.Html(
        string="Supplier Stock",
        compute="_compute_supplier_stock_info",
    )

    def _get_supplier_company(self):
        self.ensure_one()
        partner = self.order_id.partner_id
        if not self.product_id or not partner:
            return self.env["res.company"].browse()
        return (
            self.env["res.company"]
            .sudo()
            .search(
                [("partner_id", "=", partner.commercial_partner_id.id)],
                limit=1,
            )
        )

    def _get_supplier_display_stock_qty(self, product, warehouse, company, stock_field):
        return product.sudo().with_context(
            warehouse=warehouse.id,
            force_company=company.id,
        )[stock_field]

    def _get_supplier_replenishment_date(self, company):
        self.ensure_one()
        move = (
            self.env["stock.move"]
            .sudo()
            .search(
                [
                    ("product_id", "=", self.product_id.id),
                    ("company_id", "=", company.id),
                    ("location_id.usage", "!=", "internal"),
                    ("location_dest_id.usage", "=", "internal"),
                    (
                        "state",
                        "in",
                        [
                            "confirmed",
                            "waiting",
                            "assigned",
                            "partially_available",
                        ],
                    ),
                ],
                order="date",
                limit=1,
            )
        )
        return fields.Date.to_date(move.date) if move else False

    @api.depends("product_id", "order_id.partner_id")
    def _compute_supplier_stock_info(self):
        stock_field = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_order_line_stock_info.stock_field_on_sol", "qty_available")
        )
        for line in self:
            info = ""
            vendor_company = line._get_supplier_company()
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
                        total += line._get_supplier_display_stock_qty(
                            line.product_id, warehouse, vendor_company, stock_field
                        )
                    if total > 0:
                        info = f"<span>{total}</span>"
                    else:
                        replenishment_date = line._get_supplier_replenishment_date(
                            vendor_company
                        )
                        if replenishment_date:
                            label = _("Replenishment: %s") % replenishment_date
                            info = "<span>%s</span>" % label
            line.supplier_stock_info = info
