# Copyright 2016 ACSONE SA/NV, Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Ir Actions Report Multi Company',
    'summary': 'Make Report Actions multi-company aware',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/multi-company',
    'depends': [
        'base',
    ],
    'data': [
        'views/ir_actions_report_view.xml',
        'security/multi_company.xml',
    ],
}
