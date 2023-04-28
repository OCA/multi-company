# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
import logging
from collections import defaultdict
from functools import reduce
from itertools import groupby
from operator import itemgetter, or_

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _propagate_multicompany_account(self, field):
        """Set the same account for all companies.

        Args:
            field (str):
                The field to propagate. E.g. "property_account_income_id"
                or "property_account_expense_id".
        """
        sorted_products = (self - self.filtered("company_id")).sorted(field)
        if self and not sorted_products:
            raise UserError(
                _("Only multi-company products can be propagated to other companies.")
            )
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
                    sorted_products[field].mapped("code"),
                ),
            ]
        )
        accounts_map = defaultdict(dict)
        for account in alien_accounts:
            accounts_map[account.company_id.id][account.code] = account.id
        # Group products by account
        for good_account, products_grouper in groupby(
            sorted_products, itemgetter(field)
        ):
            products = reduce(or_, products_grouper)
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
                        "not exist there: products=%s, company=%s, account=%s",
                        products,
                        alien_company,
                        target_code,
                    )
                    continue
                products.with_company(alien_company)[field] = target_account_id

    def propagate_multicompany_account_income(self):
        self._propagate_multicompany_account("property_account_income_id")

    def propagate_multicompany_account_expense(self):
        self._propagate_multicompany_account("property_account_expense_id")

    @api.model_create_multi
    def create(self, vals_list):
        """Propagate accounts to other companies always, on creation."""
        res = super().create(vals_list)
        multicompany_products = res - res.filtered("company_id")
        income_products = multicompany_products.filtered("property_account_income_id")
        expense_products = multicompany_products.filtered("property_account_expense_id")
        # Skip if no account was selected
        if not income_products and not expense_products:
            return res
        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return res
        # Propagate account to other companies by default
        income_products.propagate_multicompany_account_income()
        expense_products.propagate_multicompany_account_expense()
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    def propagate_multicompany_account_expense(self):
        self.product_tmpl_id.propagate_multicompany_account_expense()

    def propagate_multicompany_account_income(self):
        self.product_tmpl_id.propagate_multicompany_account_income()
