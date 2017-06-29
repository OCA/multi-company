# coding: utf-8
# © 2017 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def create(self, vals):
        res = super(ResCompany, self).create(vals)
        self._prepare_company_creation()
        return res

    def _prepare_company_creation(self):
        """ This method will be called """
        res = super(ResCompany, self)._prepare_company_creation()
