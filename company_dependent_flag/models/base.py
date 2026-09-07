# © 2023 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        result = super().fields_get(allfields=allfields, attributes=attributes)
        classes = self._get_company_dependent_css_class()
        company_dependent_fields = [
            field_name
            for field_name, field_rec in self.env[self._name]._fields.items()
            if field_rec.company_dependent
        ]
        for field_name in result.keys() & set(company_dependent_fields):
            result[field_name]["company_dependent_css_class"] = " ".join(set(classes))
        return result

    def _get_company_dependent_css_class(self):
        """Inherit to apply your own class"""

        return ["fa", "fa-building-o"]
