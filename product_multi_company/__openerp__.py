# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': "Product multi-company",
    'summary': "Select individually the product visibility on each company",
    'author': "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              "Odoo Community Association (OCA)",
    'website': "http://serviciosbaeza.com",
    'category': 'Product Management',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'purchase',
        'sale_stock',
    ],
    'data': [
        'views/product_template_view.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
