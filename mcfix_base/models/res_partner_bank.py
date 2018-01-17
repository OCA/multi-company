from odoo import api, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.constrains('company_id')
    def _check_company_id_out_model(self):
        """Method used by other modules"""
        pass
