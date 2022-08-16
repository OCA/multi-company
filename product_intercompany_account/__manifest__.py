# Copyright 2021 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Product Intercompany Account',
    'version': '12.0.1.0.1',
    'summary': 'Change the income and COGS accounts in intercompany transactions',
    'author': 'ForgeFlow S.L., Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'depends': ['sale_stock', 'account'],
    "data": [
        "views/product_view.xml",
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
