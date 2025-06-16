# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.model
    def _get_purchase_sale_line_sync_fields(self):
        res = super()._get_purchase_sale_line_sync_fields()

        res.update({"date_planned": "commitment_date"})

        return res
