from odoo import api, models


class Currency(models.Model):
    _inherit = "res.currency"

    @api.multi
    def amount_to_text(self, amount):
        """Related to https://github.com/odoo/odoo/pull/22851"""
        if len(self) == 0:
            return False
        return super(Currency, self).amount_to_text(amount=amount)
