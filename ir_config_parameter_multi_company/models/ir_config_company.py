from odoo import fields, models


class IrConfigCompany(models.Model):
    _name = "ir.config_parameter_company"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
    )

    company_value = fields.Char(
        required=True,
        string="Value",
    )

    config_parameter_id = fields.Many2one(
        "ir.config_parameter",
        string="Config Parameter",
    )
