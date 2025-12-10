# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MulticompanyViewRestriction(models.Model):
    _name = "multicompany.view.restriction"
    _description = "Multicompany View Restriction"

    model_id = fields.Many2one("ir.model", required=True, ondelete="cascade")
    name = fields.Char(related="model_id.model", store=True)
    active = fields.Boolean(default=True)
