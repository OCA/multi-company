# -*- encoding: utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
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
    'name' : 'Product automatic company',
    'version' : '1.0',
    "author" : "Savoir-faire Linux",
    "website" : "http://www.savoirfairelinux.com",
    'license': 'AGPL-3',
    'category' : 'Sales',
    'depends' : ['product', 'stock'],
    'description': """
This module:
    * Makes company field mandatory on product
    * Sets the default value to the company of the user session
    * Hides the field to the user.
""",
    'data' : ['product_autocompany_view.xml'],
    'auto_install': False,
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

