# Copyright 2023 Moduon Team S.L.
# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_multicompany_product_pricelist_key(self):
        return "name"

    def propagate_multicompany_product_pricelist(self):
        self._propagate_multicompany_field("property_product_pricelist")

    def _propagate_property_fields(self):
        """Propagate product pricelist to other companies always, on creation."""
        super()._propagate_property_fields()
        multicompany_partners = self - self.filtered("company_id")
        pricelist_partners = multicompany_partners.filtered(
            "property_product_pricelist"
        )
        # Skip if no pricelist was selected
        if not pricelist_partners:
            return
        # Skip if user has access to only one company
        alien_user_companies = self.env.user.company_ids - self.env.company
        if not alien_user_companies:
            return
        # Propagate pricelist to other companies by default
        pricelist_partners.propagate_multicompany_product_pricelist()
