from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    intercompany_in_type_id = fields.Many2one(
        "stock.picking.type", string="Intercompany operation type"
    )
