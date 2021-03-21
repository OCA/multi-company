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
    address_for_company_ids = fields.One2many(
        "res.company",
        "partner_id",
        "Address for Company",
    )

    @api.depends("parent_id", "address_for_company_ids")
    def _compute_intercompany_readonly_shared(self):
        for record in self:
            record.intercompany_readonly_shared = (
                record.address_for_company_ids
                or record.parent_id.intercompany_readonly_shared
            )
