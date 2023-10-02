# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
import logging
from collections import defaultdict

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    same_name_other_companies = fields.Boolean(
        compute="_compute_same_name_other_companies",
        help="Whether this model can be propagated to other companies.",
    )

    def _compute_same_name_other_companies(self):
        for record in self:
            alien_companies = self.env.user.company_ids - self.company_id
            companies_chart_template_equal = (
                alien_companies - self.company_id
            ).filtered(
                lambda c: c.chart_template_id == self.company_id.chart_template_id
            )
            self = self.with_context(
                allowed_company_ids=companies_chart_template_equal.ids
                + self.company_id.ids
            )
            record.same_name_other_companies = bool(
                self.search_count(
                    [
                        ("company_id", "in", companies_chart_template_equal.ids),
                        ("name", "=", self.name),
                    ]
                )
            )

    def _propagated_fields(self):
        """Fields to propagate to other companies."""
        return [
            "rule_type",
            "auto_reconcile",
            "to_check",
            "matching_order",
            "match_text_location_label",
            "match_text_location_note",
            "match_text_location_reference",
            "match_nature",
            "match_amount",
            "match_amount_min",
            "match_amount_max",
            "match_label",
            "match_label_param",
            "match_note",
            "match_note_param",
            "match_transaction_type",
            "match_transaction_type_param",
            "match_same_currency",
            "allow_payment_tolerance",
            "payment_tolerance_param",
            "payment_tolerance_type",
            "match_partner",
            "match_partner_ids",
            "match_partner_category_ids",
            "past_months_limit",
            "number_entries",
        ]

    def propagate_to_other_companies(self):
        """Set the same value for all companies with same chart template."""
        alien_companies = self.env.user.company_ids - self.company_id

        # Filter companies with same chart template
        companies_chart_template_equal = (alien_companies - self.company_id).filtered(
            lambda c: c.chart_template_id == self.company_id.chart_template_id
        )
        if not companies_chart_template_equal:
            raise UserError(
                _(
                    "There are no other companies to propagate to. "
                    "Make sure you have access to other companies "
                    "that share the same chart of accounts."
                )
            )

        self = self.with_context(
            allowed_company_ids=companies_chart_template_equal.ids + self.company_id.ids
        )

        # Map accounts by company and code
        accounts_map = self._get_account_map_propagate(companies_chart_template_equal)

        # Map taxes by company and name
        taxes_map = self._get_taxes_map_propagate(companies_chart_template_equal)

        # Propagate to other companies
        for company in companies_chart_template_equal:
            rec_model = self.search(
                [("company_id", "=", company.id), ("name", "=", self.name)]
            )
            if rec_model:
                for field in self._propagated_fields():
                    rec_model[field] = self[field]
            else:
                rec_model = self.create(self._get_vals_create_propagated(company))

            # Update lines
            rec_model._propagate_line_ids(
                self.line_ids, company, accounts_map, taxes_map
            )

            # Update partner mapping lines
            rec_model._propagate_partner_mapping_line_ids(
                self.partner_mapping_line_ids, company
            )
        return {
            "effect": {
                "type": "rainbow_man",
                "message": _(
                    "Congratulations! Has been created/update %s reconciles models"
                )
                % len(companies_chart_template_equal),
            }
        }

    def _get_account_map_propagate(self, companies):
        """Get map accounts by company and code from accounts in line_ids."""
        accounts = self.env["account.account"].search(
            [
                ("company_id", "in", companies.ids),
                (
                    "code",
                    "in",
                    self.line_ids.account_id.mapped("code"),
                ),
            ]
        )
        accounts_map = defaultdict(dict)
        for account in accounts:
            accounts_map[account.company_id.id][account.code] = account.id
        return accounts_map

    def _get_taxes_map_propagate(self, companies):
        """Get map taxes by company and name from taxes in line_ids."""
        taxes = self.env["account.tax"].search(
            [
                ("company_id", "in", companies.ids),
                (
                    "name",
                    "in",
                    self.line_ids.tax_ids.mapped("name"),
                ),
            ]
        )
        taxes_map = defaultdict(dict)
        for tax in taxes:
            taxes_map[tax.company_id.id][tax.name] = tax.id
        return taxes_map

    def _get_vals_create_propagated(self, company):
        """Get values to create a new account.reconcile.model."""
        vals = {
            "name": self.name,
            "company_id": company.id,
        }
        vals.update({field: self[field] for field in self._propagated_fields()})
        return vals

    def _propagate_line_ids(self, lines, company, accounts_map, taxes_map):
        """Propagate lines"""
        if not lines:
            return
        rec_model_lines_ids = []
        for line in lines:
            try:
                target_account = accounts_map[company.id][line.account_id.code]
            except KeyError:
                _logger.warning(
                    "Not propagating account to company because it does "
                    "not exist there: company=%s, account=%s",
                    company,
                    line.account_id.code,
                )
                continue
            target_taxes_ids = []
            for tax in line.tax_ids:
                try:
                    target_taxes_ids.append(taxes_map[company.id][tax.name])
                except KeyError:
                    _logger.warning(
                        "Not propagating tax to company because it does "
                        "not exist there: company=%s, tax=%s",
                        company,
                        tax.name,
                    )
                    continue
            rec_model_lines_ids.append(
                self.env["account.reconcile.model.line"]
                .create(
                    {
                        "model_id": self.id,
                        "sequence": line.sequence,
                        "account_id": target_account,
                        "label": line.label,
                        "amount_type": line.amount_type,
                        "force_tax_included": line.force_tax_included,
                        "amount_string": line.amount_string,
                        "tax_ids": [(6, 0, target_taxes_ids)],
                    }
                )
                .id
            )
        self.update(
            {
                "line_ids": [(6, 0, rec_model_lines_ids)],
            }
        )

    def _propagate_partner_mapping_line_ids(self, partner_mapping_lines, company):
        """Propagate partner mapping lines"""
        if not partner_mapping_lines:
            return
        rec_model_partners = self.env["account.reconcile.model.partner.mapping"].create(
            [
                {
                    "model_id": self.id,
                    "partner_id": line.partner_id.id,
                    "payment_ref_regex": line.payment_ref_regex,
                    "narration_regex": line.narration_regex,
                }
                for line in partner_mapping_lines
            ]
        )
        self.update(
            {
                "partner_mapping_line_ids": [(6, 0, rec_model_partners.ids)],
            }
        )
