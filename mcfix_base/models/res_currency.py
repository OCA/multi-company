from odoo import api, models


class Currency(models.Model):
    _inherit = "res.currency"

    @api.multi
    def amount_to_text(self, amount):
        if len(self) == 0:
            return False
        return super(Currency, self).amount_to_text(amount=amount)
