# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    invoice_auto_validation = fields.Boolean(
        related="company_id.invoice_auto_validation",
        string="Invoices Auto Validation",
        readonly=False,
        help="When an invoice is created by a multi company rule for "
        "this company, it will automatically validate it.",
    )
    intercompany_invoice_user_id = fields.Many2one(
        related="company_id.intercompany_invoice_user_id",
        readonly=False,
        help="Responsible user for creation of invoices triggered by "
        "intercompany rules. If not set the user initiating the"
        "transaction will be used",
    )
    company_share_product = fields.Boolean(
        "Share product to all companies",
        help="Share your product to all companies defined in your instance.\n"
        " * Checked : Product are visible for every company, "
        "even if a company is defined on the partner.\n"
        " * Unchecked : Each company can see only its product "
        "(product where company is defined). Product not related to a "
        "company are visible for all companies.",
    )

    intercompany_invoicing = fields.Boolean(
        string="Generate Inter company Invoices",
        related="company_id.intercompany_invoicing",
        help="Enable intercompany invoicing: "
        "\n * Generate a Customer Invoice when a bill with this company is created."
        "\n * Generate a Vendor Bill when an invoice with this company as a customer"
        " is created.",
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        product_rule = self.env.ref("product.product_comp_rule")
        res.update(
            company_share_product=not bool(product_rule.active),
        )
        return res

    def set_values(self):
        res = super().set_values()
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.write({"active": not bool(self.company_share_product)})
        return res
