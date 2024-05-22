# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import api, models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_multicompany_delivery_carrier_key(self):
        return "name"

    def propagate_multicompany_delivery_carrier(self):
        self._propagate_multicompany_field("property_delivery_carrier_id")

    @api.model_create_multi
    def create(self, vals_list):
        """Propagate delivery carrier to other companies always, on creation."""
        res = super().create(vals_list)
        multicompany_partners = res - res.filtered("company_id")
        delivery_partners = multicompany_partners.filtered(
            "property_delivery_carrier_id"
        )
        # Skip if no delivery was selected
        if not delivery_partners:
            return res
        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return res
        # Propagate delivery carrier to other companies by default
        delivery_partners.propagate_multicompany_delivery_carrier()
        return res
