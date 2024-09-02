from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Field need to be stored to be used in search view
    country_id = fields.Many2one(store=True)
    # Other fields are also not stored, but we need to store them to avoid the following warning:
    # UserWarning: res.company: inconsistent 'store' for computed fields,
    # accessing street, street2, zip, city, state_id may recompute and update country_id.
    # Use distinct compute methods for stored and non-stored fields.
    street = fields.Char(store=True)
    street2 = fields.Char(store=True)
    zip = fields.Char(store=True)
    city = fields.Char(store=True)
    state_id = fields.Many2one(store=True)
