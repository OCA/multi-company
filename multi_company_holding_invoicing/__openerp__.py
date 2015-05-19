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

{
    'name': 'Multi Company Holding Invoicing',
    'version': '0.1',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': "",
    'description': """
    """,
    'author': 'Akretion',
    'website': 'http://www.akretion.com/',
    'depends': [
        'stock_picking_invoice_link',
        'inter_company_rules'
    ],
    'data': [
        'data/stock_account_data.xml',
        'sales_team_view.xml',
        'stock_view.xml',
        'account_invoice_view.xml',
        'security/stock_security.xml',
    ],
    'installable': True,
}
