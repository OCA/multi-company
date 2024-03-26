# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _inter_company_create_invoice(self, dest_company):
        res = super()._inter_company_create_invoice(dest_company)
        if res["dest_invoice"].move_type == "in_invoice":
            self._link_invoice_purchase(res["dest_invoice"])
        return res

    def _link_invoice_purchase(self, dest_invoice):
        self.ensure_one()
        orders = self.env["purchase.order"]
        for line in dest_invoice.invoice_line_ids:
            line.purchase_line_id = (
                line.auto_invoice_line_id.sale_line_ids.auto_purchase_line_id
            )
        orders = dest_invoice.invoice_line_ids.purchase_line_id.order_id
        if orders:
            message = _("This vendor bill is related with: {}").format(
                ",".join([o._get_html_link(o.name) for o in orders])
            )
            dest_invoice.message_post(body=Markup(message))
