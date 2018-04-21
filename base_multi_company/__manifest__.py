# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Multi Company Base',
    'summary': 'Provides a base for adding multi-company support to models.',
    'version': '10.0.2.0.0',
    'author': "LasLabs, Tecnativa, Odoo Community Association (OCA)",
    'category': 'base',
    'website': 'https://laslabs.com',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'pre_init_hook': 'create_company_assignment_view',
    'data': [
        'security/ir.model.access.csv',
    ],
}
