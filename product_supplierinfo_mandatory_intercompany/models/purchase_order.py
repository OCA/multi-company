# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    missing_inter_supplierinfo_message = fields.Html(
        readonly=True, compute="_compute_missing_intercompany_supplierinfo"
    )

    line_missing_inter_supplierinfo_ids = fields.Many2many(
        comodel_name="product.product",
        readonly=True,
        compute="_compute_missing_intercompany_supplierinfo",
    )

    @api.depends(
        "order_line.product_id",
        "order_line.product_qty",
        "partner_id.commercial_partner_id",
    )
    def _compute_missing_intercompany_supplierinfo(self):
        company_partners = self.env["res.company"].sudo().search([]).partner_id
        for order in self:
            message = ""
            missing_rules = self.env["product.product"]
            dest_company = order.partner_id.commercial_partner_id
            if dest_company in company_partners:
                intercompany_pricelist = self._get_intercompany_pricelist(
                    order.partner_id.commercial_partner_id, dest_company
                )
                lines = order.order_line.filtered(lambda l: l.product_id)
                products_qty_partner = [
                    (line.product_id, line.product_qty, order.partner_id)
                    for line in lines
                ]
                rules = intercompany_pricelist._compute_price_rule(
                    products_qty_partner, fields.Date.today()
                )
                for product_id, (_price, rule) in rules.items():
                    if not rule:
                        missing_rules += self.env["product.product"].browse(product_id)
                if missing_rules:
                    message = _(
                        "No intercompany supplierinfo found for the following products: %s. "
                        "Contact the company %s to create an item on "
                        "the intercompany pricelist %s for these products. "
                        "Or remove the products from the order."
                    ) % (
                        ", ".join(missing_rules.mapped("display_name")),
                        dest_company.name,
                        intercompany_pricelist.name,
                    )
            order.missing_inter_supplierinfo_message = message
            order.line_missing_inter_supplierinfo_ids = missing_rules

    def button_confirm(self):
        self.env["res.company"].sudo().search([]).partner_id
        for order in self:
            if order.line_missing_inter_supplierinfo_ids:
                raise UserError(
                    _(
                        "You cannot confirm this order because it contains products "
                        "without intercompany supplierinfo. Please resolve the issue "
                        "before confirming the order."
                    )
                )
        return super().button_confirm()
