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
        if company_id:
            self.flush_model(["key", "value", "company_id"])
            self.env.cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s "
                "AND (company_id = %s OR company_id IS NULL)",
                [key, company_id],
            )
            result = self.env.cr.fetchone()
            return result and result[0]
        else:
            return super()._get_param(key)
