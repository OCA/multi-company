# Copyright 2018 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Stock Move Line Multi Company Security',
    'summary': 'Adds security to Stock Move Lines across companies',
    'version': '12.0.1.0.1',
    'category': 'Stock',
    'author': 'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/multi-company',
    'license': 'AGPL-3',
    'depends': [
        'stock',
    ],
    'data': [
        'security/stock_security.xml',
    ],
    'application': False,
    'installable': True,
}
