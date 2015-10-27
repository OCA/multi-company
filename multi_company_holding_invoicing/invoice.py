# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2015 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, fields, api
from openerp.exceptions import Warning as UserError
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _holding_sale_count(self):
        self.holding_sale_count = len(self.holding_sale_ids)

    company_sale_ids = fields.One2many('sale.order', 'holding_company_id')
    holding_sale_ids = fields.One2many('sale.order', 'holding_invoice_id')
    holding_sale_count = fields.Integer(compute='_holding_sale_count',
                                        string='# of Sales Order')

    @api.multi
    def unlink(self):
        sale_obj = self.env['sale.order']
        sales = sale_obj.search([('holding_invoice_id', 'in', self.ids)])
        res = super(AccountInvoice, self).unlink()
        #We use an SQL request here for solving perf issue
        if sales:
            self._cr.execute("""UPDATE sale_order
                SET holding_invoice_state = '2binvoiced'
                WHERE id in %s""", (tuple(sales.ids),))
        return res
