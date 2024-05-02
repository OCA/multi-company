# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
import logging
from collections import defaultdict
from functools import reduce
from itertools import groupby
from operator import itemgetter, or_

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_multicompany_account_account_key(self):
        return "code"

    def _get_multicompany_account_fiscal_position_key(self):
        return "name"

    def _get_multicompany_account_payment_term_key(self):
        return "name"

    def _get_multicompany_domain_by_key(self, field, key):
        # eg. _get_multicompany_account_account_key
        return [
            (
                key,
                "in",
                self.mapped(f"{field}.{key}"),
            ),
        ]

    def _propagate_multicompany_m2o_by_key(self, field):
        """Set the corresponding record accross all companies
        based on a domain to match record on other comanies

        eg. account are matched by code
        """
        companies = self._get_alien_companies()
        comodel = self._fields[field].comodel_name
        # eg. _get_multicompany_account_account_key
        key_func = f"_get_multicompany_{comodel.replace('.', '_')}_key"
        key = getattr(self, key_func)()
        domain_key = self._get_multicompany_domain_by_key(field, key)
        domain = expression.AND([[("company_id", "in", companies.ids)], domain_key])
        # Gain access to all companies of current user
        alien_records = self.env[comodel].search(domain)
        self = self.with_context(
            allowed_company_ids=self.env.company.ids + companies.ids
        )
        records_map = defaultdict(dict)
        for record in alien_records:
            records_map[record.company_id.id][record[key]] = record.id
        # Group partner by record key
        for good_record, partners_grouper in groupby(self, itemgetter(field)):
            partners = reduce(or_, partners_grouper)
            # Propagate record by key to alien companies if possible
            target_key = good_record[key]
            for alien_company in companies:
                try:
                    # False is a valid value, if you want to remove the position
                    target_record = (
                        target_key and records_map[alien_company.id][target_key]
                    )
                except KeyError:
                    description = self.env[comodel]._description
                    _logger.warning(
                        "Not propagating %s to company because it does"
                        " not exist there: Partners=%s, Company=%s, %s=%s",
                        description,
                        partners,
                        alien_company,
                        description,
                        target_key,
                    )
                    continue
                partners.with_company(alien_company)[field] = target_record

    def _propagate_multicompany_m2o(self, field):
        """Propagate a property record to other companies

        If the related record is without company, set the same.
        otherwise try to match it.
        """
        company_specific = self.filtered(f"{field}.company_id")
        company_shared = self - company_specific
        company_specific._propagate_multicompany_m2o_by_key(field)
        company_shared._propagate_multicompany_value(field)

    def _propagate_multicompany_value(self, field):
        """Set the same value accross all companies"""
        # Gain access to all companies of current user
        companies = self._get_alien_companies()
        self = self.with_context(
            allowed_company_ids=self.env.company.ids + companies.ids
        )
        # Group partner by record
        for value, partners_grouper in groupby(self, itemgetter(field)):
            partners = reduce(or_, partners_grouper)
            for alien_company in companies:
                partners.with_company(alien_company)[field] = value

    def _get_alien_companies(self):
        alien_companies = self.env.user.company_ids - self.env.company
        if not alien_companies:
            raise UserError(
                _(
                    "There are no other companies to propagate to. "
                    "Make sure you have access to other companies."
                )
            )
        return alien_companies

    def _propagate_multicompany_field(self, field):
        """Set the same account for all companies.

        Args:
            field (str):
                The field to propagate. E.g. "property_account_payable_id"
                or "property_account_receivable_id".
        """
        sorted_partners = (self - self.filtered("company_id")).sorted(field)
        if self and not sorted_partners:
            raise UserError(
                _("Only multi-company partner can be propagated to other companies.")
            )
        if hasattr(self[field], "company_id"):
            sorted_partners._propagate_multicompany_m2o(field)
        else:
            sorted_partners._propagate_multicompany_value(field)

    def propagate_multicompany_account_payable(self):
        self._propagate_multicompany_field("property_account_payable_id")

    def propagate_multicompany_account_receivable(self):
        self._propagate_multicompany_field("property_account_receivable_id")

    def propagate_multicompany_account_position(self):
        self._propagate_multicompany_field("property_account_position_id")

    def propagate_multicompany_payment_term_id(self):
        self._propagate_multicompany_field("property_payment_term_id")

    def propagate_multicompany_supplier_payment_term_id(self):
        self._propagate_multicompany_field("property_supplier_payment_term_id")

    @api.model_create_multi
    def create(self, vals_list):
        """Propagate accounts to other companies always, on creation."""
        res = super().create(vals_list)
        multicompany_partners = res - res.filtered("company_id")
        payable_partners = multicompany_partners.filtered("property_account_payable_id")
        receivable_partners = multicompany_partners.filtered(
            "property_account_receivable_id"
        )
        position_partners = multicompany_partners.filtered(
            "property_account_position_id"
        )
        payment_term_partners = multicompany_partners.filtered(
            "property_payment_term_id"
        )
        payment_term_partners = multicompany_partners.filtered(
            "property_payment_term_id"
        )
        supplier_payment_term_partners = multicompany_partners.filtered(
            "property_supplier_payment_term_id"
        )
        if (
            payable_partners
            and not receivable_partners
            and not position_partners
            and not position_partners
            and not payment_term_partners
            and not supplier_payment_term_partners
        ):
            return res
        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return res
        # Propagate account to other companies by default
        payable_partners.propagate_multicompany_account_payable()
        receivable_partners.propagate_multicompany_account_receivable()
        position_partners.propagate_multicompany_account_position()
        payment_term_partners.propagate_multicompany_payment_term_id()
        supplier_payment_term_partners.propagate_multicompany_supplier_payment_term_id()
        return res
