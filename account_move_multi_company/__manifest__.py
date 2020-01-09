# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Multicompany',
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': 'Open Source Integrators, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/multi-company',
    'license': 'AGPL-3',
    'depends': [
        'account_invoice_consolidated',
    ],
    'data': [
        'views/account_move_view.xml',
    ],
    'installable': True,
    'development_status': 'Beta',
    'maintainers': [
        'max3903',
    ]
}
