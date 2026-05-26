# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class UtmSource(models.Model):
    _inherit = "utm.source"

    _sql_constraints = [
        (
            "unique_name",
            "UNIQUE(name, company_id)",
            "The name must be unique per company",
        ),
    ]

    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.company,
        ondelete="cascade",
    )
