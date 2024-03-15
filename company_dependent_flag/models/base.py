# © 2023 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import xml.dom.minidom as minidom

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super()._fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == "form":
            arch = minidom.parseString(res["arch"])
            self._update_company_dependent_css(arch)
            res["arch"] = arch.toxml()
        return res

    def _update_company_dependent_css(self, arch):
        cpny_dep_fields = [
            field_name
            for field_name, field_rec in self.env[self._name]._fields.items()
            if field_rec.company_dependent
        ]
        for field_name in cpny_dep_fields:
            for field in arch.getElementsByTagName("field"):
                if field.getAttribute("name") == field_name:
                    # Create a new div element
                    div = arch.createElement("div")
                    div.setAttribute("class", "o_row")

                    # Create a new span element
                    span = arch.createElement("span")
                    span.setAttribute(
                        "class",
                        "fa fa-lg fa-building-o",
                    )
                    span.setAttribute("title", "Values set here are company-specific.")

                    # Check if a label already exists for the field
                    existing_labels = arch.getElementsByTagName("label")

                    if not any(
                        label.getAttribute("for") == field.getAttribute("name")
                        for label in existing_labels
                    ):
                        # Create a new label element

                        label = arch.createElement("label")
                        label.setAttribute("for", field.getAttribute("name"))
                        label.setAttribute("class", "o_form_label")
                        label.appendChild(
                            arch.createTextNode(field.getAttribute("string"))
                        )

                        # Insert the label before the field in the parent node
                        field.parentNode.insertBefore(label, field)

                    div.appendChild(span)
                    div.appendChild(field.cloneNode(True))

                    # Replace the field with the new div
                    field.parentNode.replaceChild(div, field)
