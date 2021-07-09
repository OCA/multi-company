# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailTemplate(models.Model):

    _inherit = "mail.template"

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        ondelete="set null",
    )
