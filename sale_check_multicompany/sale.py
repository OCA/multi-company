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


class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    def _check_pricelist(self, cr, uid, ids):
        for elm in self.browse(cr, uid, ids):
            if elm.pricelist_id:
                if isinstance(elm.company_id, orm.browse_null) \
                        or not elm.company_id:
                    company_id = self.pool['res.company']._company_default_get(
                        cr, uid, 'sale.order')
                    company = self.pool['res.company'].browse(
                        cr, uid, company_id)
                else:
                    company = elm.company_id
                if elm.pricelist_id.company_id.id != company.id:
                    raise orm.except_orm(
                        "Invalid Pricelist",
                        "The pricelist defined in this quotation is linked "
                        "to '%s' company\n"
                        "whereas the quotation is linked to '%s'"
                        "\nChoose a pricelist which match to the company '%s'"
                        % (elm.pricelist_id.company_id.name,
                           company.name, company.name))
        return True

    _constraints = [(_check_pricelist, 'Error', ['pricelist_id'])]
