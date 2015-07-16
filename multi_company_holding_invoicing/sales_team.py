# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 AKRETION (<http://www.akretion.com>).
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
from openerp import fields, models


class CrmCaseSection(models.Model):
    _inherit = 'crm.case.section'

    holding_company_id = fields.Many2one(
        'res.company', string='Holding Company for Invoicing',
        help="Select the holding company to invoice")
    holding_customer_automatic_invoice = fields.Boolean(
        string='Holding customer',
        help="Check this box to invoice automatically the holding's customers "
             "from delivery orders completed")
    holding_supplier_automatic_invoice = fields.Boolean(
        string='Holding supplier',
        help="Check this box to invoice automatically the holding's suppliers "
             "from delivery orders completed")
