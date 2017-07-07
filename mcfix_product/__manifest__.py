# -*- coding: utf-8 -*-
# Copyright 2017 Creu Blanca.
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Mcfix Product',
    'version': '10.0.1.0.0',
    'summary': 'Provides product fixes for multi-company management',
    'author': 'Creu Blanca,'
              'Eficent,'
              'Odoo Community Association (OCA)',
    'category': 'base',
    'website': 'https://github.com/OCA/multi-company',
    'license': 'LGPL-3',
    'depends': ['product'],
    'data': [
        'views/product_views.xml',
        'views/product_supplierinfo_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
