# Copyright 2018-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MultiCompanyAbstractTester(models.Model):
    _name = "multi.company.abstract.tester"
    _inherit = "multi.company.abstract"

    name = fields.Char()
