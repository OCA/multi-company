# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _should_bypass_reservation(self, forced_location=False):
        """For Company B's reception moves, we want the transactions to be in the
        "assigned" status so that we can validate the delivery note directly and/or
        have it automatically validated once the reception process from Company A
        is complete.
        For Company A's delivery transactions, we want them to be in the "assigned"
        status so that we can validate them if necessary.
        """
        res = super()._should_bypass_reservation(forced_location=forced_location)
        location = forced_location or self.location_id
        # RMA Receiver
        rma_receiver = self.sudo().rma_receiver_ids
        if rma_receiver and rma_receiver.intercompany_origin_rma_id:
            if location == rma_receiver._get_location_final():
                return True
        # RMA Delivery
        rma = self.sudo().rma_id
        if rma and rma.intercompany_rma_id:
            if location == rma.intercompany_rma_id._get_location_final():
                return True
        return res
