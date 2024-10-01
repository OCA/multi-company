# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    consolidated_by_id = fields.Many2one(
        "account.invoice.consolidated", string="Consolidated By", readonly=True
    )
