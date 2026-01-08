# Copyright 2026 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _run_buy(self, procurements):
        last_po = self.env["purchase.order"].search(
            [],
            order="id desc",
            limit=1,
        )
        res = super()._run_buy(procurements)
        new_po = self.env["purchase.order"].search([("id", ">", last_po.id)])
        # Auto-confirm purchase orders linked to sale orders
        for purchase in new_po:
            if (
                purchase.sale_order_count
                and purchase.partner_id.ref_company_ids
                and purchase.company_id.purchase_auto_validation
            ):
                purchase.button_confirm()
        return res
