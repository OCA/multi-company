# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm, fields


class ResCurrency(orm.Model):
    _inherit = 'res.currency'

    def name_get(self, cr, uid, ids, context=None):
        """ If currencies are not shared and they have the same name,
            then display have to distinguish them"""
        result = []
        for currency in self.browse(cr, uid, ids, context):
            cpny_info = ''
            if currency.company_id:
                cpny_info = ' (%s)' % currency.company_id.name
            result.append((currency.id, '%s%s' % (currency.name, cpny_info)))
        return result


class ProductPriceType(orm.Model):
    _inherit = 'product.price.type'

    _columns = {
        'currency_id': fields.property(
            'res.currency',
            relation='res.currency',
            type='many2one',
            string='Currency',
            view_load=True,
            required=True,
            help="The currency the field is expressed in."
                 "Field redefined in field property "
                 "for multicompany purpose."),
    }
