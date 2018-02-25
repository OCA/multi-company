# Copyright 2018 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Multicompany Easy Creation',
    'summary': 'This module adds a wizard to create companies easily',
    'version': '10.0.1.0.0',
    'category': 'Uncategorized',
    'website': 'https://github.com/OCA/multi-company/tree/11.0/'
               'account_multicompany_easy_creation',
    'author': 'Tecnativa, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
        'account',
    ],
    'data': [
        'wizards/multicompany_easy_creation.xml',
    ],
}
