from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def get_base_url(self):
        if "company_id" in self._fields:
            company = self.company_id
        else:
            company = self.env.company
        return super(
            BaseModel, self.with_context(force_config_parameter_company=company)
        ).get_base_url()
