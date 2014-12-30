# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm
from openerp.tools.translate import _


class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    def _check_pricelist(self, cr, uid, ids):
        for elm in self.browse(cr, uid, ids):
            if elm.pricelist_id:
                if elm.company_id:
                    company = elm.company_id
                else:
                    company_id = self.pool['res.company']._company_default_get(
                        cr, uid, 'sale.order')
                    company = self.pool['res.company'].browse(
                        cr, uid, company_id)
                if elm.pricelist_id.company_id.id != company.id:
                    raise orm.except_orm(
                        _("Invalid Pricelist"),
                        _("The pricelist defined in this quotation is linked "
                          "to '%s' company\n"
                          "whereas the quotation is linked to '%s'\n"
                          "\nChoose a pricelist which match "
                          "to the company '%s'")
                        % (elm.pricelist_id.company_id.name,
                           company.name, company.name))
        return True

    _constraints = [(_check_pricelist, 'Error', ['pricelist_id'])]
