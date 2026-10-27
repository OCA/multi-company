# Copyright (C) 2026-TODAY NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# @author Nils Coenen <nils.coenen@nico-solutions.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompanyRepresentative(models.Model):
    _name = "res.company.representative"
    _description = "Representative for Company"
    _order = "sequence asc"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
    )
    representative_role_id = fields.Many2one(
        "res.company.representative.role",
        string="Representative Role",
        required=True,
    )
    sequence = fields.Integer(
        help="Used to order representatives.",
    )

    _unique_representative = models.Constraint(
        "unique(company_id, partner_id)",
        "A representative cannot be assigned to the same company multiple times.",
    )

    @api.model
    def _get_sequence(self, company_id):
        last_representative = self.search(
            [
                ("company_id", "=", company_id),
                ("sequence", "!=", False),
            ],
            order="sequence desc",
            limit=1,
        )

        return (last_representative.sequence or 0) + 1

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("company_id"):
                vals["company_id"] = self.env.company.id

            if not vals.get("sequence"):
                vals["sequence"] = self._get_sequence(vals["company_id"])

        return super().create(vals_list)
