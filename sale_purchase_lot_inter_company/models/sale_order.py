# Copyright (c) 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_purchase_order_line_data(
        self, sale_line, dest_company, purchase_order
    ):
        vals = super()._prepare_purchase_order_line_data(
            sale_line, dest_company, purchase_order
        )
        if dest_company.propagated_serial_number_so_po and sale_line.lot_id:
            vals["lot_id"] = sale_line.lot_id.get_inter_company_lot(dest_company).id
        return vals
