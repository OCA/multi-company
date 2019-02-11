# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    'name': 'Product Supplier Intercompany',
    'version': '8.0.0.0.1',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'author': "Akretion",
    'website': 'https://akretion.com',
    'depends': [
        'product_variant_supplierinfo',
    ],
    'data': [
        'views/pricelist_views.xml',
        'security/ir.rule.csv',
    ],
    'demo': [
        'demo/pricelist.xml',
    ],
    'installable': True,
}
