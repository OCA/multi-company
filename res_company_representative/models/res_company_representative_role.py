# Copyright (C) 2026-TODAY NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# @author Nils Coenen <nils.coenen@nico-solutions.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompanyRepresentativeRole(models.Model):
    _name = "res.company.representative.role"
    _description = "Representative Role for Company"

    name = fields.Char(
        string="Role Name",
        required=True,
        translate=True,
    )

    _unique_role_name = models.Constraint(
        "unique(name)",
        "The representative role name must be unique.",
    )
