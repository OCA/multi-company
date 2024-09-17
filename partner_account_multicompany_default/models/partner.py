# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import api, models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_multicompany_account_account_key(self):
        return "code"

    def _get_multicompany_account_fiscal_position_key(self):
        return "name"

    def _get_multicompany_account_payment_term_key(self):
        return "name"

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
