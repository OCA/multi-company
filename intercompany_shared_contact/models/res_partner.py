# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    intercompany_readonly_shared = fields.Boolean(
        compute="_compute_intercompany_readonly_shared",
        compute_sudo=True,
        store=True,
    )

    @api.depends("parent_id")
    def _compute_intercompany_readonly_shared(self):
        partners = self.env["res.company"].search([]).partner_id
        for record in self:
            record.intercompany_readonly_shared = (
                record in partners or record.parent_id.intercompany_readonly_shared
            )
