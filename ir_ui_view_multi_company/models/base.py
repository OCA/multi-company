# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class Model(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type="form", **options):
        """view cache dependent on the company"""
        key = super()._get_view_cache_key(view_id, view_type, **options)
        return key + (self.env.company,)
