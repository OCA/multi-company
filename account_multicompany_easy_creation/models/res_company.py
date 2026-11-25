# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class Company(models.Model):
    _inherit = "res.company"

    def install_l10n_modules(self):
        if self.env.context.get("skip_install_l10n_modules"):
            # Specifically want to avoid this behavior if we use the company
            # creation wizard
            return False
        return super().install_l10n_modules()
