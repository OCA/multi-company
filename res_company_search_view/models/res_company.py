from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    street = fields.Char(store=True)
    street2 = fields.Char(store=True)
    zip = fields.Char(store=True)
    city = fields.Char(store=True)
    state_id = fields.Many2one(store=True)
    country_id = fields.Many2one(store=True)
