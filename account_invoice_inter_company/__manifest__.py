# -*- coding: utf-8 -*-
# © 2013-2014 Odoo SA
# © 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Inter Company Module for Invoices',
    'summary': 'Intercompany invoice rules',
    'version': '10.0.1.1.0',
    'category': 'Accounting & Finance',
    'website': 'http://www.odoo.com',
    'author': 'Odoo SA, Akretion, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
        'account_accountant',
        'onchange_helper',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/res_config_view.xml',
    ],
    'demo': [
        'demo/inter_company_invoice.xml',
    ],
}
