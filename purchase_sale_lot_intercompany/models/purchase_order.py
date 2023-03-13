# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_sale_order_line_data(self, purchase_line, dest_company, sale_order):
        line_vals = super()._prepare_sale_order_line_data(purchase_line, dest_company, sale_order)
        if dest_company.propagated_serial_number:
            original_so_line = purchase_line.sale_line_id
            if original_so_line.lot_id:
                original_lot = original_so_line.lot_id
                destination_lot = original_lot.get_inter_company_lot(dest_company)
                if destination_lot:
                    line_vals.update(lot_id=destination_lot.id)
        return line_vals
