from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    property_account_income_intercompany = fields.Many2one(
        comodel_name="account.account",
        company_dependent=True,
        string="Income Intercompany Account",
        help="Income account used for intercompany transactions."
    )
    property_account_expense_intercompany = fields.Many2one(
        comodel_name="account.account",
        company_dependent=True,
        string="Expense Intercompany Account",
        help="Expense account used for intercompany transactions."
    )

    @api.multi
    def get_product_intercompany_accounts(self):
        return {
            'income': (
                self.property_account_income_intercompany or
                self.categ_id.property_account_income_categ_intercompany
            ),
            'expense': (
                self.property_account_expense_intercompany or
                self.categ_id.property_account_expense_categ_intercompany
            ),
        }
