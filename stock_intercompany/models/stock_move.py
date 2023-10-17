from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self):
        """
        Override to create counterpart pickings after moves are assigned.
        """
        res = super()._action_assign()

        counterparts = self.mapped("picking_id")._create_counterpart_pickings("out")

        for picking, counterpart in counterparts:
            picking._finalize_counterpart_picking(counterpart)
        return res
