# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _inter_company_create_invoice(self, dest_company):
        res = super()._inter_company_create_invoice(dest_company)
        if res["dest_invoice"].type == "in_invoice":
            # Link intercompany purchase order with intercompany invoice
            self._link_invoice_purchase(res["dest_invoice"])
        return res

    def _link_invoice_purchase(self, dest_invoice):
        self.ensure_one()
        orders = self.env["purchase.order"]
        vals = {}
        for line in dest_invoice.invoice_line_ids:
            vals["invoice_lines"] = [(4, line.id)]
            purchase_lines = line.auto_invoice_line_id.sale_line_ids.mapped(
                "auto_purchase_line_id"
            )
            purchase_lines.update(vals)
            orders |= purchase_lines.mapped("order_id")
        if orders:
            ref = "<a href=# data-oe-model=purchase.order data-oe-id={}>{}</a>"
            message = _(
                "This vendor bill is related with: {}".format(
                    ",".join([ref.format(o.id, o.name) for o in orders])
                )
            )
            dest_invoice.message_post(body=message)
