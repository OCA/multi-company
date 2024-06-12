# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def propagate_multicompany_purchase_currency(self):
        # currency are shared acrosse companies
        self._propagate_multicompany_field("property_purchase_currency_id")

    def _propagate_property_fields(self):
        """Propagate accounts to other companies always, on creation."""
        super()._propagate_property_fields()
        multicompany_partners = self - self.filtered("company_id")
        purchase_currency_partners = multicompany_partners.filtered(
            "property_purchase_currency_id"
        )
        # Skip if no currency was selected
        if not purchase_currency_partners:
            return
        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return
        # Propagate account to other companies by default
        purchase_currency_partners.propagate_multicompany_purchase_currency()
