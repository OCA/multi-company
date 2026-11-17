# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2025 Batista10
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup

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
        for line in dest_invoice.invoice_line_ids:
            line.sale_line_ids = (
                line.auto_invoice_line_id.purchase_line_id.auto_sale_line_id
            )
        orders = dest_invoice.invoice_line_ids.sale_line_ids.order_id
        if orders:
            message = _("This customer invoice is related with: {}").format(
                ",".join([o._get_html_link(o.name) for o in orders])
            )
            dest_invoice.message_post(body=Markup(message))
