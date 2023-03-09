# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _inter_company_create_invoice(self, dest_company):
        res = super()._inter_company_create_invoice(dest_company)
        if res["dest_invoice"].move_type == "out_invoice":
            self._link_invoice_sale(res["dest_invoice"])
        return res

    def _link_invoice_sale(self, dest_invoice):
        self.ensure_one()
        orders = self.env["sale.order"]
        for line in dest_invoice.invoice_line_ids:
            purchase_line = line.auto_invoice_line_id.purchase_line_id
            line.sale_line_ids = [(6, 0, purchase_line.auto_sale_line_id.ids)]
        orders = dest_invoice.invoice_line_ids.sale_line_ids.order_id
        if orders:
            ref = "<a href=# data-oe-model=sale.order data-oe-id={}>{}</a>"
            message = _("This customer bill is related with: {}").format(
                ",".join([ref.format(o.id, o.name) for o in orders])
            )
            dest_invoice.message_post(body=message)
