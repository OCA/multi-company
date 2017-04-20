# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Inter Company Module for Purchase to Sale Order',
    'summary': 'Intercompany PO/SO rules',
    'version': '8.0.1.0.0',
    'category': 'Purchase Management',
    'website': 'http://www.odoo.com',
    'author': 'Odoo SA, Akretion, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
        'sale',
        'purchase',
        'account_invoice_inter_company',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/res_config_view.xml',
        'views/purchase_order_view.xml',
    ],
    'demo': [
        'demo/inter_company_purchase_sale.xml',
    ],
}
