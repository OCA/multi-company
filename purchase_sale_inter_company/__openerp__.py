# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Inter Company Module for Purchase to Sale Orders',
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
        'sale_stock',
        'sale_order_dates',
        'account_invoice_inter_company'
    ],
    'data': [
        'views/inter_company_po_to_so_view.xml',
        'views/res_config_view.xml',
    ],
    'test': [
        'test/test_intercompany_data.yml',
        'test/inter_company_po_to_so.yml',
    ],
}
