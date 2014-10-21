# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: David BEAL
#    Copyright 2014 Akretion
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
    'name': 'Unshared Currency Multicompany',
    'version': '0.1',
    'category': '',
    'sequence': 10,
    'summary': "Currency settings multicompany",
    'description': """
This module should be used if your companies have their currencies non shared.
Currencies cannot be shared because 'res.currency.rate' doesn't have
a company_id field
This also implies that each company must have their own price lists
    """,
    'author': 'Akretion',
    'website': 'http://www.akretion.com',
    'depends': [
        'product',
        ],
    'data': [
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'images': [
    ],
    'css': [
    ],
    'js': [
    ],
    'qweb': [
    ],
}
