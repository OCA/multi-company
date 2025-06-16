# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_sale_order_line_data(self, purchase_line, dest_company, sale_order):
        res = super()._prepare_sale_order_line_data(
            purchase_line, dest_company, sale_order
        )

        res.update({"commitment_date": purchase_line.date_planned})

        return res
