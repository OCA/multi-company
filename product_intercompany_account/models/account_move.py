from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        res = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        our_companies = self.env["res.company"].search(
            [("partner_id", "=", self.partner_id.id)]
        )
        for i_line in res:
            product_level = i_line.product_id.property_account_expense_intercompany
            categ = i_line.product_id.categ_id.property_account_expense_categ_intercompany
            if our_companies and (product_level or categ):
                accounts = i_line.product_id.product_tmpl_id.get_product_accounts()
                for item in res:
                    if item["account_id"] == accounts["expense"].id:
                        item["account_id"] = product_level.id or categ.id
        return res

    def _prepare_account_move_line(self, line):
        data = super(AccountMove, self)._prepare_account_move_line(line)
        is_intercompany = self.env["res.company"].search(
            [("partner_id", "=", self.partner_id.id,)]
        )

        if is_intercompany:
            inter_company_accounts = (
                line.product_id.product_tmpl_id.get_product_intercompany_accounts()
            )
            if type in ("out_invoice", "out_refund"):
                data["account_id"] = inter_company_accounts["income"].id
            else:
                data["account_id"] = inter_company_accounts["expense"].id
        return data
