from odoo import api, models


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.constrains('company_id')
    def _check_company_id_out_model(self):
        self._check_company_id_base_model()
