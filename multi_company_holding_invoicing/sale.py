# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 AKRETION
#    @author Chafique Delli <chafique.delli@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        section_id = vals.get('section_id', False)
        if section_id:
            section = self.env['crm.case.section'].browse(section_id)
            if section.invoicing_partner_id:
                vals['order_policy'] = 'picking'
        return super(SaleOrder, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'section_id' in vals:
            section_id = vals.get('section_id')
            section = self.env['crm.case.section'].browse(section_id)
            if section.invoicing_partner_id:
                vals.update({
                    'order_policy': 'picking'
                })
            else:
                vals.update({
                    'order_policy': 'manual'
                })
        return super(SaleOrder, self).write(vals)
