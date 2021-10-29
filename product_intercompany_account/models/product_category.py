from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    property_account_income_categ_intercompany = fields.Many2one(
        comodel_name="account.account",
        company_dependent=True,
        string="Income Intercompany Account",
        help="Income account used for intercompany transactions."
    )
    property_account_expense_categ_intercompany = fields.Many2one(
        comodel_name="account.account",
        company_dependent=True,
        string="Expense Intercompany Account",
        help="Expense account used for intercompany transactions."
    )
