# Copyright 2026 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    @api.depends("product_id.company_id", "product_id.company_ids")
    def _compute_company_id(self):
        # For lots belonging to single-company products, defer to standard logic.
        # For multi-company products, preserve the stored company_id so that a
        # change to product.company_ids (e.g. adding a third company) never
        # overwrites the lot's original company — which would cause _check_unique_lot
        # to fire when two lots share the same name across different companies.
        single_company_lots = self.filtered(
            lambda rec: len(rec.product_id.sudo().company_ids) == 1
        )
        res = super(StockLot, single_company_lots)._compute_company_id()
        for lot in self - single_company_lots:
            lot.company_id = lot._origin.company_id or lot.product_id.company_id
        return res
