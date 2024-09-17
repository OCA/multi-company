# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_multicompany_account_payment_mode_key(self):
        return "name"

    def propagate_multicompany_customer_payment_mode(self):
        self._propagate_multicompany_field("customer_payment_mode_id")

    def propagate_multicompany_supplier_payment_mode(self):
        self._propagate_multicompany_field("supplier_payment_mode_id")

    def _propagate_property_fields(self):
        """Propagate accounts to other companies always."""
        super()._propagate_property_fields()

        customer_payment_mode_partners = self.filtered("customer_payment_mode_id")
        supplier_payment_mode_partners = self.filtered("supplier_payment_mode_id")
        if not customer_payment_mode_partners and not supplier_payment_mode_partners:
            return

        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return

        # Propagate payment_mode to other companies by default
        customer_payment_mode_partners.propagate_multicompany_customer_payment_mode()
        supplier_payment_mode_partners.propagate_multicompany_supplier_payment_mode()
