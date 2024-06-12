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
    """Adds helpers to create default values across companies

    For each M2O property field for records that are not shared, define:

    def _get_multicompany_account_account_key(self):
        return "code"

    Where account_account is the model and code is the key on which you want
    to match a similar record on an other company.

    Also add a method like

    def propagate_multicompany_account_payable(self):
        self._propagate_multicompany_field("property_account_payable_id")

    That you can add in the view to let the user trigger the synchronisation for
    a specific field.

    """

    _inherit = "res.partner"

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

    def _propagate_property_fields(self):
        return

    @api.model_create_multi
    def create(self, vals_list):
        """Propagate property values on creation to other companies."""
        res = super().create(vals_list)
        multicompany_partners = res - res.filtered("company_id")
        multicompany_partners._propagate_property_fields()
        return res

    def write(self, vals):
        """If forced, propagate property values on update to other companies."""
        res = super().write(vals)
        # Allow opt-in for progagation on write using context
        # Useful for data import to update records
        if (
            self.env.context.get("force_property_propagation")
            and "property_propagation" not in self.env.context
        ):
            multicompany_partners = self - self.filtered("company_id")
            # avoid infinite loop
            ctx = {"property_propagation": "ongoing"}
            multicompany_partners = multicompany_partners.with_context(**ctx)
            multicompany_partners._propagate_property_fields()
        return res
