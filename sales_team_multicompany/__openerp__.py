# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Sales Team Multicompany',
    'summary': 'Add companies in sales team and '
               'filter the sales team from the company',
    'version': '9.0.0.1.0',
    'category': 'Sales Management',
    'website': 'http://akretion.com',
    'author': 'Akretion',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'depends': [
        'sale',
    ],
    'data': [
        'sales_team.xml',
        'security/ir.rule.csv',
    ],
    'demo': [
        'demo/res.company.csv',
        'demo/res.partner.csv',
        'demo/res.users.csv',
        'demo/crm.team.csv',
    ],
    'qweb': [
    ]
}
