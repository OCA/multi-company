# Copyright 2023- Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class EventTag(models.Model):
    _inherit = "event.tag"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        change_default=True,
        default=lambda self: self.env.company,
        required=False,
    )
    # ------------------------------------------------------
    # SQL Constraints
    # ------------------------------------------------------

    # ------------------------------------------------------
    # Default methods
    # ------------------------------------------------------

    # ------------------------------------------------------
    # Computed fields / Search Fields
    # ------------------------------------------------------

    # ------------------------------------------------------
    # Onchange / Constraints
    # ------------------------------------------------------

    # ------------------------------------------------------
    # CRUD methods (ORM overrides)
    # ------------------------------------------------------

    # ------------------------------------------------------
    # Actions
    # ------------------------------------------------------

    # ------------------------------------------------------
    # Business methods
    # ------------------------------------------------------
