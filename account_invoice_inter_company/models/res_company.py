# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

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
    intercompany_invoicing = fields.Boolean(
        string="Generate Inter company Invoices",
        help="Enable intercompany invoicing: "
        "\n* Generate a Customer Invoice when a bill with this company is created."
        "\n* Generate a Vendor Bill when an invoice with this company as a customer"
        " is created.",
        default=True,
    )

    def _get_user_domain(self):
        self.ensure_one()
        group_account_invoice = self.env.ref("account.group_account_invoice")
        return [
            ("id", "!=", self.env.ref("base.user_root").id),
            ("company_ids", "=", self.id),
            ("id", "in", group_account_invoice.users.ids),
        ]
