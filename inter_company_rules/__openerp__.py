# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    'name': 'Inter Company Module for Sale/Purchase Orders and Invoices',
    'version': '8.0.1.1.0',
    'summary': 'Intercompany SO/PO/INV rules',
    'author': 'Odoo SA, Odoo Community Association (OCA)',
    'website': 'http://www.odoo.com',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'purchase',
        'sale_stock',
        'sale_order_dates'
    ],
    'data': [
        'views/inter_company_so_po_view.xml',
        'views/res_config_view.xml',
    ],
    'test': [
        'test/test_intercompany_data.yml',
        'test/inter_company_so_to_po.yml',
        'test/inter_company_po_to_so.yml',
        'test/inter_company_invoice.yml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
