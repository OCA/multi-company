from odoo import fields, models


class MultiCompanyRelationTester(models.Model):
    _name = "multi.company.relation.tester"
    _inherit = "multi.company.abstract"
    _description = "Multi Company Relation Tester"

    name = fields.Char()
