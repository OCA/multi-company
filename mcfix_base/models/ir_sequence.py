# Copyright 2018 Creu Blanca
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, models


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.constrains('company_id')
    def _check_company_id_out_model(self):
        self._check_company_id_base_model()
