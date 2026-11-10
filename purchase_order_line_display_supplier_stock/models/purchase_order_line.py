# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    display_qty_supplier_widget = fields.Boolean(
        compute="_compute_qty_supplier_widget",
    )
    qty_supplier_issue = fields.Boolean(
        compute="_compute_qty_supplier_widget",
    )
    qty_supplier_widget_data = fields.Binary(
        compute="_compute_qty_supplier_widget",
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
        return (
            product.sudo()
            .with_company(company)
            .with_context(warehouse_id=warehouse.id)[stock_field]
        )

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
        return fields.Date.to_date(move.date) if move else "Not scheduled yet"

    @api.depends("product_id", "order_id.partner_id")
    def _compute_qty_supplier_widget(self):
        stock_field = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_order_line_stock_info.stock_field_on_sol", "qty_available")
        )
        for line in self:
            res = {}
            total = 0
            vendor_company = line._get_supplier_company()
            product = line.product_id
            line.display_qty_supplier_widget = (
                product.type == "consu" and product.is_storable
            )
            warehouses = self.env["stock.warehouse"].search(
                [
                    ("company_id", "=", vendor_company.id),
                    ("display_stock_on_sol", "=", True),
                ]
            )
            if warehouses:
                for warehouse in warehouses:
                    total += line._get_supplier_display_stock_qty(
                        product, warehouse, vendor_company, stock_field
                    )
                res = {
                    "vendor_name": vendor_company.display_name,
                    "qty": total,
                    # TODO compute date if free = 0 and virtual > 0
                    "date": line._get_supplier_replenishment_date(vendor_company)
                    if not total
                    else fields.Date.today(),
                }
            line.qty_supplier_issue = False if total else True
            line.qty_supplier_widget_data = res
