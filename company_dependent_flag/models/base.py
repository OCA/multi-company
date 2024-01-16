# © 2023 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            self._update_company_dependent_css(arch)
        return arch, view

    def _update_company_dependent_css(self, arch):
        cpny_dep_fields = [
            field_name
            for field_name, field_rec in self.env[self._name]._fields.items()
            if field_rec.company_dependent
        ]
        for field_name in cpny_dep_fields:
            for field in arch.xpath(f"//field[@name='{field_name}']"):
                classes = field.attrib.get("class", "").split(" ")
                classes += self._get_company_dependent_css_class()
                field.attrib["class"] = " ".join(set(classes))

    def _get_company_dependent_css_class(self):
        """Inherit to apply your own class"""

        return ["fa", "fa-building-o", "d-flex", "flex-row"]
