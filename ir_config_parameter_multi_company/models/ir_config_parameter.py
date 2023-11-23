from odoo import api, fields, models


class IrConfigMultiCompany(models.Model):
    _inherit = "ir.config_parameter"

    company_value_ids = fields.One2many(
        "ir.config_parameter_company",
        "config_parameter_id",
        string="Company",
        required=False,
    )

    # how to test? Check here
    # https://www.odoo.com/documentation/14.0/developer/reference/cli.html#shell
    # https://www.odoo.com/documentation/15.0/developer/reference/backend/testing.html
    @api.model
    def _get_param(self, key):
        params = self.search([("key", "=", key)])
        if params and params.company_value_ids:
            values = params.company_value_ids
            for value in values:
                if value.company_id == self.env.user.company_id:
                    return value.company_value
        return super(IrConfigMultiCompany, self)._get_param(key)
