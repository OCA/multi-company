from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_account_id(self):
        super()._compute_account_id()
        intercompany_partners = (
            self.env["res.company"]
            .sudo()
            .search([("partner_id", "in", self.mapped("partner_id").ids)])
            .mapped("partner_id")
        )
        intercompany_product_lines = self.filtered(
            lambda line: line.display_type == "product"
            and line.move_id.is_invoice(True)
            and line.product_id
            and line.partner_id in intercompany_partners
        )
        for intercompany_product_line in intercompany_product_lines:
            tmpl = intercompany_product_line.product_id.product_tmpl_id
            inter_company_accounts = tmpl.get_product_intercompany_accounts()
            if intercompany_product_line.move_id.is_sale_document(
                include_receipts=True
            ):
                intercompany_product_line.account_id = (
                    inter_company_accounts["income"]
                    or intercompany_product_line.account_id
                )
            elif intercompany_product_line.move_id.is_purchase_document(
                include_receipts=True
            ):
                intercompany_product_line.account_id = (
                    inter_company_accounts["expense"]
                    or intercompany_product_line.account_id
                )
        return
