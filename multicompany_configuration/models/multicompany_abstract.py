# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from odoo import fields, models


class MulticompanyAbstract(models.AbstractModel):
    _name = "multicompany.abstract"
    _description = "Abstract model that allows multicompany easy configuration"

    multicompany_data = fields.Serialized(
        prefetch=False,
        compute="_compute_multicompany_data",
        inverse="_inverse_multicompany_data",
    )

    def _multicompany_field_permissions(self):
        """
        Extra hook that allows us to set specific groups for company_dependent fields
        By default, we add all the modifications for odoo company dependent fields

        """
        return {}

    def _multicompany_field_attrs(self):
        """
        Extra hook that allows us to set specific groups for company_dependent fields
        Changing widget is not correctly supported if special data is needed :S
        """
        return {}

    def _compute_multicompany_data(self):
        companies = self.env.companies
        company_fields = {
            field_name: field
            for field_name, field in self._fields.items()
            if field.company_dependent
        }
        field_permissions = self._multicompany_field_permissions()
        field_attrs = self._multicompany_field_attrs()
        for record in self:
            multicompany_data = {
                "companies": companies.name_get(),
                "data": {c.id: {} for c in companies},
                "fields": {},
            }
            for field_name, field in company_fields.items():
                if field_name in field_permissions:
                    if not self.user_has_groups(field_permissions[field_name]):
                        continue
                if field.groups:
                    if not self.user_has_groups(field.groups):
                        continue
                for company in companies:
                    company_record = record.with_company(company.id)
                    multicompany_data["data"][company.id][
                        field_name
                    ] = field.convert_to_read(
                        company_record[field_name], company_record
                    )

                multicompany_data["fields"][field_name] = self._get_field_info(
                    field_name, field, field_attrs
                )
            record.multicompany_data = multicompany_data

    def _get_field_info(self, field_name, field, field_attrs):
        attrs = self._get_field_attrs(field)
        attrs.update(field_attrs.get(field_name, {}))
        result = {
            "type": field.type,
            "attrs": attrs,
        }
        if isinstance(field, fields.Float):
            result["digits"] = json.dumps(field.get_digits(self.env))
        return result

    def _get_field_attrs(self, field):
        if isinstance(field, fields._Relational):
            return {"domain": field.get_domain_list(self)}
        return {}

    def _inverse_multicompany_data(self):
        for record in self:
            for company_id, vals in record.multicompany_data["data"].items():
                company_record = record.with_company(company_id)
                new_vals = {}
                for field, val in vals.items():
                    if isinstance(val, list):
                        val = tuple(val)
                    field_class = self._fields[field]
                    if (
                        field_class.convert_to_read(
                            company_record[field], company_record
                        )
                        != val
                    ):
                        new_vals[field] = field_class.convert_to_write(
                            val, company_record
                        )
                if new_vals:
                    company_record.write(new_vals)

    def get_multicompany_action(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            self._get_multicompany_action_xml_id()
        )
        action.update({"res_id": self.id})
        return action

    def _get_multicompany_action_xml_id(self):
        pass

    def action_apply_multicompany_changes(self):
        return {}
