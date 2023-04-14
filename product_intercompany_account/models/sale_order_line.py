from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        our_companies = self.env['res.company'].sudo().search(
            [('partner_id', '=', self.order_id.partner_id.id)]
        )
        product = self.product_id.with_context(force_company=self.company_id.id)
        product_level = product.property_account_income_intercompany
        categ = product.categ_id.property_account_income_categ_intercompany
        if our_companies and (product_level or categ):
            account = product_level or categ
            res.update({'account_id': account.id})
        return res
