# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrincipalModelFake(models.Model):
    _name = "principal.model.fake"
    _description = "Primary fake model for tests"
    _inherit = "company.check.mixin"

    def _allowed_company_get_fields_to_check(self):
        return ["secondary_ids"]

    name = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
    secondary_ids = fields.One2many(
        comodel_name="secondary.model.fake",
        inverse_name="primary_id",
        string="Secondary",
    )


class SecondaryModelFake(models.Model):
    _name = "secondary.model.fake"
    _description = "Secondary fake model for tests"

    name = fields.Char()
    primary_id = fields.Many2one(
        comodel_name="principal.model.fake",
        string="Primary",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
