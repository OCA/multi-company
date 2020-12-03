# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    company_share_product = fields.Boolean(
        "Share product to all companies",
        compute="_compute_share_product",
        compute_sudo=True,
    )
    invoice_auto_validation = fields.Boolean(
        help="When an invoice is created by a multi company rule "
        "for this company, it will automatically validate it",
        default=True,
    )
    intercompany_invoice_user_id = fields.Many2one(
        "res.users",
        string="Inter Company Invoice User",
        help="Responsible user for creation of invoices triggered by "
        "intercompany rules.",
    )

    def _compute_share_product(self):
        product_rule = self.env.ref("product.product_comp_rule")
        for company in self:
            company.company_share_product = not bool(product_rule.active)

    def _get_user_domain(self):
        self.ensure_one()
        group_account_invoice = self.env.ref("account.group_account_invoice")
        return [
            ("id", "!=", self.env.ref("base.user_root").id),
            ("company_ids", "=", self.id),
            ("id", "in", group_account_invoice.users.ids),
        ]
