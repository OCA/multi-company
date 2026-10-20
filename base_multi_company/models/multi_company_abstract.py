# Copyright 2017 LasLabs Inc.
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.models import TableSQL
from odoo.orm.identifiers import NewId
from odoo.tools import SQL

_logger = logging.getLogger(__name__)


class MultiCompanyAbstract(models.AbstractModel):
    _name = "multi.company.abstract"
    _description = "Multi-Company Abstract"

    company_id = fields.Many2one(
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
    @api.depends_context("allowed_company_ids", "company", "_check_company_source_id")
    def _compute_company_id(self):
        for record in self:
            # Set this priority computing the company (if included in the allowed ones)
            # for avoiding multi company incompatibility errors:
            # - If this call is done from method _check_company, the company of the
            #   record to be compared.
            # - Otherwise, use current companies of the user, prioritizing main company.
            # - As last resource, use the first allowed company.
            company_id = self.env.context.get("_check_company_source_id")
            if company_id in record.company_ids.ids:
                record.company_id = company_id
            else:
                common_companies = self.env.companies & record.company_ids
                # Prioritize main company
                if common_companies and (self.env.company in common_companies):
                    record.company_id = self.env.company.id
                # Or use the first common company
                elif common_companies:
                    record.company_id = common_companies[0].id
                else:  # Use the fallback as last resource
                    company = record.company_ids[:1]
                    if company and isinstance(company.id, NewId):
                        record.company_id = company._origin.id or False
                    else:
                        record.company_id = company.id

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

    def _order_field_to_sql(
        self,
        table: TableSQL,
        field_expr: str,
        direction: SQL,
        nulls: SQL,
    ) -> SQL:
        """Skip ``company_id`` in ORDER BY instead of raising."""
        fname = field_expr.split(":", 1)[0].split(".", 1)[0]
        field = self._fields.get(fname)
        if fname == "company_id" and field is not None and not field.store:
            _logger.debug(
                "%s: ignoring non-stored company_id in ORDER BY term %r.",
                self._name,
                field_expr,
            )
            return SQL()
        return super()._order_field_to_sql(table, field_expr, direction, nulls)

    def _read_group_groupby(self, table: TableSQL, groupby_spec: str) -> SQL:
        """Group on ``company_ids`` when asked to group on ``company_id``."""
        fname = groupby_spec.split(":", 1)[0].split(".", 1)[0]
        field = self._fields.get(fname)
        if fname == "company_id" and field is not None and not field.store:
            if groupby_spec != "company_id":
                raise UserError(
                    self.env._(
                        "Grouping by %(spec)s is not supported on %(model)s "
                        "because its Company field is computed from Companies. "
                        "Group by Companies instead.",
                        spec=groupby_spec,
                        model=self._name,
                    )
                )
            _logger.debug(
                "%s: grouping on company_ids instead of the non-stored company_id.",
                self._name,
            )
            return super()._read_group_groupby(table, "company_ids")
        return super()._read_group_groupby(table, groupby_spec)

    def _multicompany_patch_vals(self, vals):
        """Patch vals to remove company_id and company_ids duplicity."""
        if "company_ids" in vals and "company_id" in vals:
            company_id = vals.pop("company_id")
            if company_id:
                c_ids = vals["company_ids"]
                # Safely handle False, tuple commands, tuple-of-commands, and non-lists
                if not c_ids:
                    vals["company_ids"] = []
                elif isinstance(c_ids, tuple):
                    if c_ids and all(isinstance(item, tuple) for item in c_ids):
                        vals["company_ids"] = list(c_ids)
                    else:
                        vals["company_ids"] = [c_ids]
                elif not isinstance(c_ids, list):
                    vals["company_ids"] = [c_ids]

                vals["company_ids"].append(fields.Command.link(company_id))
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        """Discard changes in company_id field if company_ids has been given."""
        for vals in vals_list:
            # Avoid triggering the inverse write of company_id after creating a record.
            # The intermediate record has no company_ids yet, which can make
            # company-dependent record rules reject the write for users creating
            # products.
            if "company_id" in vals and "company_ids" not in vals:
                company_id = vals.pop("company_id")
                if company_id:
                    vals["company_ids"] = [fields.Command.link(company_id)]
            self._multicompany_patch_vals(vals)
        records = super().create(vals_list)
        # Same sudo / non-sudo cache concern as in write()
        records.invalidate_recordset(fnames=["company_ids"])
        return records

    def write(self, vals):
        """Discard changes in company_id field if company_ids has been given."""
        self._multicompany_patch_vals(vals)
        res = super().write(vals)
        if "company_ids" in vals:
            # Writing on the field without sudo won't update the sudo cache
            # (and vice versa) so we invalidate to ensure the sudo cache is
            # up-to-date
            self.invalidate_recordset(fnames=["company_ids"])
        return res
