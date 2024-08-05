from odoo import api, fields, models


class IrConfigMultiCompany(models.Model):
    _inherit = "ir.config_parameter"
    company_id = fields.Many2one("res.company", "Company")

    _sql_constraints = [
        ("key_uniq", "unique (key, company_id)", "Key must be unique per company.")
    ]

    @api.model
    def _get_param(self, key):
        company_id = self.env.company.id
        if self.env.context.get("force_config_parameter_company"):
            company_id = self.env.context["force_config_parameter_company"].id
        if company_id:
            self.flush_model(["key", "value", "company_id"])
            self.env.cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s "
                "AND (company_id = %s OR company_id IS NULL) "
                "ORDER BY company_id",
                [key, company_id],
            )
            result = self.env.cr.fetchone()
            return result and result[0]
        else:
            return super()._get_param(key)

    @api.model
    def set_param(self, key, value):
        company_id = self.env.company.id
        if self.env.context.get("force_config_parameter_company"):
            company_id = self.env.context["force_config_parameter_company"].id
        param = self.search([("key", "=", key)])
        if len(param) > 1 and company_id:
            param = self.search([("key", "=", key), ("company_id", "=", company_id)])
            old = param.value
            if value is not False and value is not None:
                if str(value) != old:
                    param.write({"value": value})
            else:
                param.unlink()
            return old
        else:
            return super().set_param(key, value)
