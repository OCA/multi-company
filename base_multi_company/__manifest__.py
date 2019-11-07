# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Multi Company Base',
    'summary': 'Provides a base for adding multi-company support to models.',
    'version': '12.0.1.0.1',
    'author': "LasLabs, Tecnativa, Odoo Community Association (OCA)",
    'category': 'base',
    'website': 'https://github.com/OCA/multi-company',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'pre_init_hook': 'create_company_assignment_view',
    'data': [
        'security/ir.model.access.csv',
    ],
    'development_status': 'Production/Stable',
    'maintainers': ['pedrobaeza'],
}
