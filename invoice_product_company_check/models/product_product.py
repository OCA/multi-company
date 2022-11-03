# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "company.check.mixin"]

    invoice_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        compute="_compute_invoice_line_ids",
        string="Invoice Line",
    )

    def _compute_invoice_line_ids(self):
        for rec in self:
            lines = self.env["account.move.line"].search([("product_id", "=", rec.id)])
            rec.invoice_line_ids = [(6, 0, lines.ids)]

    # Sale order_line are already check in odoo sale.
    def _allowed_company_get_fields_to_check(self):
        return ["invoice_line_ids"]
