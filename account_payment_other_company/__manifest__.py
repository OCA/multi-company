# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Payment Other Company',
    'version': '12.0.1.1.0',
    'summary': 'Create Payments for Other Companies',
    'author': 'Open Source Integrators, '
              'Odoo Community Association (OCA)',
    'category': 'Invoicing Management',
    'website': 'https://github.com/OCA/multi-company',
    'license': 'AGPL-3',
    'depends': [
        'account_invoice_consolidated'
    ],
    'data': [
        'views/account_payment.xml',
    ],
    'development_status': 'Beta',
    'maintainers': [
        'max3903',
        'osi-scampbell',
    ]
}
