from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _should_bypass_reservation(self, forced_location=False):
        # When this is a return picking, we want to bypass the reservation
        # because the stock is not yet available
        # in the intercompany location of this company
        # it is still located in the other company.
        if (
            self.picking_id._is_intercompany_return_reception()
            and self.picking_id.return_id._is_intercompany_delivery()
        ):
            return True
        return super()._should_bypass_reservation(forced_location=forced_location)
