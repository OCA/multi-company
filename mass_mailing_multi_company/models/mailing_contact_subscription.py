# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MassMailingContactListRel(models.Model):
    _inherit = "mailing.contact.subscription"

    company_id = fields.Many2one(
        "res.company", "Company", related="contact_id.company_id"
    )
