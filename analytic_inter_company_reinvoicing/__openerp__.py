# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Analytic Inter Company Reinvoicing',
    'summary': """
        Allows to reinvoice from a company to another one""",
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV, '
              'Odoo Community Association (OCA)',
    'website': 'https://acsone.eu',
    'depends': [
        'account',
        'account_invoice_inter_company',
    ],
    'data': [
        'wizards/account_invoice_analytic_reinvoicing.xml',
        'views/account_config_settings.xml',
        'views/account_invoice.xml',
        'views/account_invoice_line.xml',
        'views/res_company.xml',
    ],
    'demo': [
    ],
}
