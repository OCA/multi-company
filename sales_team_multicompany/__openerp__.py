# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Sales Team Multicompany',
    'summary': 'Add companies in sales team and '
               'filter the sales team from the company',
    'version': '9.0.1.0.0',
    'category': 'Sales Management',
    'website': 'http://akretion.com',
    'author': 'Akretion',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'sale',
    ],
    'data': [
        'sales_team.xml',
        'security/sales_team_multicompany_security.xml',
    ],
    'demo': [
        'sales_team_multicompany_demo.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
}
