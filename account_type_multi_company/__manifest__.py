# -*- coding: utf-8 -*-
# Copyright 2015 ACSONE SA/NV.
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Multi company account types",
    'summary': """
        Make account types multi-company aware""",
    'author': "ACSONE SA/NV,"
              "Noviat,"
              "Odoo Community Association (OCA)",
    'category': 'Accounting & Finance',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'security/account_account_type.xml',
        'views/account_account_type.xml',
    ],
    'installable': True,
}
