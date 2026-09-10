# Copyright (C) 2026-TODAY NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# @author Nils Coenen <nils.coenen@nico-solutions.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    representatives = fields.One2many(
        "res.company.representative",
        "company_id",
    )

    def get_representatives(self):
        representatives = self.representatives.sorted(key=lambda rep: rep.sequence)

        return [
            {
                "partner": representative.partner_id.name,
                "role": representative.representative_role_id.name,
            }
            for representative in representatives
        ]
