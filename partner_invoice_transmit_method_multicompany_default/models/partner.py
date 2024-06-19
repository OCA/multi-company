# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_multicompany_customer_invoice_transmit_method_key(self):
        return "code"

    def _get_multicompany_supplier_invoice_transmit_method_key(self):
        return "code"

    def propagate_multicompany_customer_invoice_transmit_method(self):
        self._propagate_multicompany_field("customer_invoice_transmit_method_id")

    def propagate_multicompany_supplier_invoice_transmit_method(self):
        self._propagate_multicompany_field("supplier_invoice_transmit_method_id")

    def _propagate_property_fields(self):
        """Propagate invoice transmission method to other companies always."""
        super()._propagate_property_fields()

        cust_transmit_method_partners = self.filtered(
            "customer_invoice_transmit_method_id"
        )
        suppl_transmit_method_partners = self.filtered(
            "supplier_invoice_transmit_method_id"
        )
        if not cust_transmit_method_partners and not suppl_transmit_method_partners:
            return

        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return

        # Propagate invoice transmission method to other companies by default
        cust_transmit_method_partners.propagate_multicompany_customer_invoice_transmit_method()
        suppl_transmit_method_partners.propagate_multicompany_supplier_invoice_transmit_method()
