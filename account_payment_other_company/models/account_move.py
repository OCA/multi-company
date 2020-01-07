# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post_validate(self):
        # Override to prevent ValidationError
        # Method in odoo/addons/account/models/account_move line 357
        return True
