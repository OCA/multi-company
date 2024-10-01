# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    consolidated_by_id = fields.Many2one(
        "account.invoice.consolidated",
        string="Consolidated In",
        readonly=True,
        ondelete="restrict",
        copy=False,
    )
