from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    counterpart_of_move_id = fields.Many2one("stock.move", check_company=False)
