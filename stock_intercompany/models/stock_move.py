from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _search_picking_for_assignation_domain(self):
        """
        Override to filter out moves that have a counterpart picking
        """
        domain = super()._search_picking_for_assignation_domain()
        domain += [("has_counterpart", "=", False)]

        return domain
