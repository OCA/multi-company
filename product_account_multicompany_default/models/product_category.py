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

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = "product.category"

    def _propagate_multicompany_account(self, field):
        """Set the same account for all companies.

        Args:
            field (str):
                The field to propagate. E.g. "property_account_income_categ_id"
                or "property_account_expense_categ_id".
        """
        alien_companies = self.env.user.company_ids - self.env.company
        if not alien_companies:
            raise UserError(
                _(
                    "There are no other companies to propagate to. "
                    "Make sure you have access to other companies."
                )
            )
        # Gain access to all companies of current user
        self = self.with_context(
            allowed_company_ids=self.env.company.ids + alien_companies.ids
        )
        # Map alien accounts by company and code
        alien_accounts = self.env["account.account"].search(
            [
                ("company_id", "in", alien_companies.ids),
                (
                    "code",
                    "in",
                    self[field].mapped("code"),
                ),
            ]
        )
        accounts_map = defaultdict(dict)
        for account in alien_accounts:
            accounts_map[account.company_id.id][account.code] = account.id
        # Group categories by account
        for good_account, categories_grouper in groupby(self, itemgetter(field)):
            categories = reduce(or_, categories_grouper)
            # Propagate account to alien companies if possible
            target_code = good_account.code
            for alien_company in alien_companies:
                try:
                    # False is a valid value, if you want to remove the account
                    target_account_id = (
                        target_code and accounts_map[alien_company.id][target_code]
                    )
                except KeyError:
                    _logger.warning(
                        "Not propagating account to company because it does "
                        "not exist there: product_categories=%s, company=%s, account=%s",
                        categories,
                        alien_company,
                        target_code,
                    )
                    continue
                if (
                    categories.with_company(alien_company)[field]
                    and categories.with_company(alien_company)[field].id
                    != target_account_id
                ):
                    categories.with_company(alien_company)[field] = target_account_id

    def propagate_multicompany_account_income(self):
        self._propagate_multicompany_account("property_account_income_categ_id")

    def propagate_multicompany_account_expense(self):
        self._propagate_multicompany_account("property_account_expense_categ_id")

    def _propagate_property_fields(self):
        income_categories = self.filtered("property_account_income_categ_id")
        expense_categories = self.filtered("property_account_expense_categ_id")
        # Skip if no account was selected
        if not income_categories and not expense_categories:
            return
        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return
        # Propagate account to other companies by default
        income_categories.propagate_multicompany_account_income()
        expense_categories.propagate_multicompany_account_expense()

    @api.model_create_multi
    def create(self, vals_list):
        """Propagate accounts to other companies always, on creation."""
        res = super().create(vals_list)
        res._propagate_property_fields()
        return res

    def write(self, vals):
        """If forced, propagate property values on write to other companies."""
        res = super().write(vals)
        # Allow opt-in for progagation on write using context
        # Useful for data import to update records

        if self.env.context.get("force_property_propagation"):
            self._propagate_property_fields()
        return res
