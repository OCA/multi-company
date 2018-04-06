# Copyright 2018 Creu Blanca
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, models


class Currency(models.Model):
    _inherit = "res.currency"

    @api.multi
    def amount_to_text(self, amount):
        """Related to https://github.com/odoo/odoo/pull/22851"""
        if len(self) == 0:
            return False
        return super(Currency, self).amount_to_text(amount=amount)
