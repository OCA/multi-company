# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_stock_move_vals(
        self, picking, price_unit, product_uom_qty, product_uom
    ):
        self.ensure_one()
        order_company = self.order_id.company_id
        if order_company and self.env.company != order_company:
            return super(
                PurchaseOrderLine, self.with_company(order_company)
            )._prepare_stock_move_vals(
                picking, price_unit, product_uom_qty, product_uom
            )
        return super()._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom
        )
