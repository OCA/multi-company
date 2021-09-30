# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = "res.partner"

    res_company_id = fields.One2many(
        "res.company",
        "partner_id",
        readonly=True,
        help="Effectively a One2one field to represent the corresponding res.company",
    )
    origin_company_id = fields.Many2one(
        "res.company",
        compute="_compute_origin_company_id",
        compute_sudo=True,
        store=True,
        help="Hack field to keep the information of the 'real' company_id. "
        "That way, we can share the contact by setting company_id to null, "
        "without losing any information. If null, the contact is not shared.",
        index=True,
    )

    @api.depends("res_company_id", "parent_id.origin_company_id")
    def _compute_origin_company_id(self):
        for record in self:
            if record.parent_id.origin_company_id:
                record.origin_company_id = record.parent_id.origin_company_id
                record.company_id = False
            if record.res_company_id:
                record.origin_company_id = record.res_company_id
                record.company_id = False
            else:
                record.origin_company_id = False

    def _get_company_depend_fields(self):
        return {key for key, field in self._fields.items() if field.company_dependent}

    def check_field_access_rights(self, operation, fields):
        res = super().check_field_access_rights(operation, fields)
        if self.env.su:
            return res
        if operation == "write":
            records = self.filtered(
                lambda s: s.origin_company_id
                and s.origin_company_id not in self.env.companies
            )
            if records:
                # We try to modify intercompany partner for a company
                #  where we do not have the access right
                forbidden_fields = set(fields) - self._get_company_depend_fields()
                if forbidden_fields:
                    fields_name = ", ".join(
                        [
                            _(field.string)
                            for fieldname, field in self._fields.items()
                            if fieldname in forbidden_fields
                        ]
                    )
                    raise AccessError(
                        _(
                            "You do not have the right to modify the field: %s for an "
                            "intercompany contact"
                        )
                        % fields_name
                    )
        return res
