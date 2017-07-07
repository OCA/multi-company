# -*- coding: utf-8 -*-
# Copyright 2017 Creu Blanca.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Mcfix Base',
    'version': '10.0.1.0.0',
    'summary': 'Provides a base fix for multi-company management',
    'author': 'Creu Blanca,'
              'Odoo Community Association (OCA)',
    'category': 'base',
    'website': 'https://github.com/OCA/multi-company',
    'depends': ['base'],
    'data': [
        'views/res_partner.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
