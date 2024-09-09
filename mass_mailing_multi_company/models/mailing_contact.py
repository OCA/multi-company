# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class MassMailingContact(models.Model):
    _inherit = "mailing.contact"

    company_id = fields.Many2one("res.company", "Company")
