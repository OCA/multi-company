from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        our_companies = self.env["res.company"].search(
            [("partner_id", "=", self.order_id.partner_id.id)]
        )
        product = self.product_id.with_company(self.company_id)
        product_level = product.property_account_income_intercompany
        categ = product.categ_id.property_account_income_categ_intercompany
        if our_companies and (product_level or categ):
            account = product_level or categ
            res.update({"account_id": account.id})
        return res
