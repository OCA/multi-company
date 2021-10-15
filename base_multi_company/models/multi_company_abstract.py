# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

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
        default=lambda self: self._default_company_ids(),
    )

    no_company_ids = fields.Boolean(
        string="No Companies",
        compute="_compute_no_company_ids",
        compute_sudo=True,
        store=True,
        index=True,
    )

    def _inverse_company_id(self):
        # To allow modifying allowed companies by non-aware base_multi_company
        # through company_id field we:
        # - Add company to company_ids if not in existing ones (not removing
        # existing ones as people that write company_id field has maybe
        # no access to other ones.)
        # - Remove all companies if company_id is False (give access to all)

        for record in self:
            company = record.company_id
            if company and company not in record.company_ids:
                record.company_ids = [(4, company.id)]
            elif not company:
                record.company_ids = [(5,)]

    @api.depends("company_ids")
    def _compute_no_company_ids(self):
        for record in self:
            if record.company_ids:
                record.no_company_ids = False
            else:
                record.no_company_ids = True

    def _default_company_ids(self):
        return self.browse(self.env.company.ids)

    @api.depends("company_ids")
    @api.depends_context("company")
    def _compute_company_id(self):
        for record in self:
            # Give the priority of the current company of the user to avoid
            # multi company incompatibility errors.
            company_id = self.env.context.get("force_company") or self.env.company.id
            if company_id in record.company_ids.ids:
                record.company_id = company_id
            else:
                record.company_id = record.company_ids[:1].id

    def _search_company_id(self, operator, value):
        return [("company_ids", operator, value)]

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        # In some situations the 'in' operator is used with company_id in a
        # name_search. ORM does not convert to a proper WHERE clause when using
        # the 'in' operator.
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
        if args:
            for arg in args:
                if type(arg) == list and arg[:2] == ["company_id", "in"]:
                    fix = []
                    for _i in range(len(arg[2]) - 1):
                        fix.append("|")
                    for val in arg[2]:
                        fix.append(["company_id", "=", val])
                    new_args.extend(fix)
                else:
                    new_args.append(arg)
        return super()._name_search(
            name,
            args=new_args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )
