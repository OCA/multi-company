# Copyright 2017 LasLabs Inc.
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import warnings

from odoo import api, fields, models


class MultiCompanyAbstract(models.AbstractModel):
    _name = "multi.company.abstract"
    _description = "Multi-Company Abstract"

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        compute="_compute_company_id",
        search="_search_company_id",
        inverse="_inverse_company_id",
    )
    company_ids = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
    )

    @api.depends("company_ids")
    @api.depends_context("company", "_check_company_source_id")
    def _compute_company_id(self):
        for record in self:
            # Set this priority computing the company (if included in the allowed ones)
            # for avoiding multi company incompatibility errors:
            # - If this call is done from method _check_company, the company of the
            #   record to be compared.
            # - Otherwise, current company of the user.
            company_id = (
                self.env.context.get("_check_company_source_id")
                or self.env.context.get("force_company")
                or self.env.company.id
            )
            if company_id in record.company_ids.ids:
                record.company_id = company_id
            else:
                record.company_id = record.company_ids[:1].id

    def _inverse_company_id(self):
        # To allow modifying allowed companies by non-aware base_multi_company
        # through company_id field we:
        # - Remove all companies, then add the provided one
        for record in self:
            record.company_ids = [(6, 0, record.company_id.ids)]

    def _search_company_id(self, operator, value):
        domain = [("company_ids", operator, value)]
        new_op = {"in": "=", "not in": "!="}.get(operator)
        if new_op and (False in value or None in value):
            # We need to workaround an ORM issue to find records with no company
            domain = ["|", ("company_ids", new_op, False)] + domain
        return domain

    def _multicompany_patch_vals(self, vals):
        """Patch vals to remove company_id and company_ids duplicity."""
        if "company_ids" in vals and "company_id" in vals:
            company_id = vals.pop("company_id")
            if company_id:
                vals["company_ids"].append(fields.Command.link(company_id))
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        """Discard changes in company_id field if company_ids has been given."""
        for vals in vals_list:
            self._multicompany_patch_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        """Discard changes in company_id field if company_ids has been given."""
        self._multicompany_patch_vals(vals)
        return super().write(vals)

    @api.model
    def _patch_company_domain(self, args):
        warnings.warn("This method is deprecated.", DeprecationWarning, stacklevel=2)
        # In some situations the 'in' operator is used with company_id in a
        # name_search or search_read.
        # ORM does not convert to a proper WHERE clause when using the 'in' operator.
        # e.g: ```
        #     WHERE "res_partner"."id" in (SELECT "res_partner_id"
        #     FROM "res_company_res_partner_rel" WHERE "res_company_id" IN (False, 1)
        # ```
        # patching the args to expand the cumbersome args int a OR clause fix
        # the issue.
        # e.g: ```
        #     WHERE "res_partner"."id" not in (SELECT "res_partner_id"
        #             FROM "res_company_res_partner_rel"
        #             where "res_partner_id" is not null)
        #         OR  ("res_partner"."id" in (SELECT "res_partner_id"
        #             FROM "res_company_res_partner_rel" WHERE "res_company_id" IN 1)
        # ```
        new_args = []
        if args is None:
            args = []
        for arg in args:
            if (isinstance(arg, list) or isinstance(arg, tuple)) and list(arg[:2]) == [
                "company_id",
                "in",
            ]:
                fix = []
                for _i in range(len(arg[2]) - 1):
                    fix.append("|")
                for val in arg[2]:
                    fix.append(["company_id", "=", val])
                new_args.extend(fix)
            else:
                new_args.append(arg)
        return new_args
