from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_partner_shipping_id = fields.Many2one(
        related="auto_invoice_id.partner_shipping_id",
        string="Source Invoice Delivery Address",
        store=True,
        readonly=True,
    )
