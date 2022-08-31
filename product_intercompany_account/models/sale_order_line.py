from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self):
        res = super()._prepare_invoice_line()

        our_companies = self.env["res.company"].search(
            [("partner_id", "=", self.order_id.partner_id.id)]
        )
        product_level = self.product_id.property_account_income_intercompany
        categ = self.product_id.categ_id.property_account_income_categ_intercompany
        if our_companies and (product_level or categ):
            account = product_level or categ
            res.update({"account_id": account.id})
        return res
