# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_multicompany_delivery_carrier_key(self):
        return "name"

    def propagate_multicompany_delivery_carrier(self):
        self._propagate_multicompany_field("property_delivery_carrier_id")

    def _propagate_property_fields(self):
        """Propagate delivery carrier to other companies always, on creation."""
        super()._propagate_property_fields()
        multicompany_partners = self - self.filtered("company_id")
        delivery_partners = multicompany_partners.filtered(
            "property_delivery_carrier_id"
        )
        # Skip if no delivery was selected
        if not delivery_partners:
            return
        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return
        # Propagate delivery carrier to other companies by default
        delivery_partners.propagate_multicompany_delivery_carrier()
