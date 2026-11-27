# Copyright 2026 XXP LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """
        Add allow_single_company to session_info.
        """
        result = super().session_info()
        user = self.env.user
        if user._is_internal():
            result["allow_single_company"] = user._single_active_company_limit_active()
        return result
