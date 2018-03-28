from odoo import api, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.constrains('company_id')
    def _check_company_id_out_model(self):
        self._check_company_id_base_model()
