# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Bill Line Distribution',
    'version': '12.0.1.0.0',
    'summary': 'Distribute AP Invoices across multiple companies',
    'author': 'Open Source Integrators, '
              'Odoo Community Association (OCA)',
    'category': 'Invoicing Management',
    'website': 'https://github.com/OCA/multi-company',
    'license': 'AGPL-3',
    'depends': [
        'account_invoice_consolidated',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/account_invoice.xml',
    ],
    'development_status': 'Beta',
    'maintainers': [
        'max3903',
        'osi-scampbell',
    ]
}
