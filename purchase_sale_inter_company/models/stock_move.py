# Copyright 2023 ForgeFlow
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _update_extra_data_in_move(self, move):
        if hasattr(self, "_cal_move_weight"):  # from delivery module
            self._cal_move_weight()


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _update_extra_data_in_move_line(self, move_line):
        pass
