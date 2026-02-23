# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        move_values = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if values.get("rma_receiver_ids"):
            rma_ids = values.get("rma_receiver_ids")[0][2]
            rma = self.env["rma"].browse(rma_ids)
            if rma.intercompany_rma_id:
                # It is important to define the correct destination location. You cannot
                # define this location in the corresponding RMA because that would imply
                # that no rule was found in the RMA IN route. Creating a rule with the
                # Intercompany destination location would not be a solution, as it would
                # have many unintended consequences.
                location = rma.intercompany_rma_id._get_location_final()
                move_values["location_dest_id"] = location.id
            elif rma.intercompany_origin_rma_id:
                intercompany_rma = (
                    rma.intercompany_origin_rma_id.sudo().intercompany_rma_id
                )
                move_values["location_id"] = intercompany_rma._get_location_final().id
        elif values.get("rma_id"):
            rma = self.env["rma"].browse(values.get("rma_id"))
            if rma.intercompany_rma_id:
                location = rma.intercompany_rma_id.sudo()._get_location_final()
                move_values["location_id"] = location.id
        return move_values
