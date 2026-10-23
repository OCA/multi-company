# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_sale_order_line_data(self, purchase_line, dest_company, sale_order):
        vals = super()._prepare_sale_order_line_data(
            purchase_line, dest_company, sale_order
        )
        if dest_company.propagated_serial_number and purchase_line.lot_id:
            lot = purchase_line.lot_id.sudo()
            if lot.company_id:
                lot.company_id = False
            vals["lot_id"] = lot.id
        return vals
