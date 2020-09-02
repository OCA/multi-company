# Copyright 2017-2019 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Product Tax Multi Company Default',
    'version': '12.0.1.0.0',
    'category': 'Account',
    'website': 'https://www.tecnativa.com',
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'product',
    ],
    'data': [
        'views/product_template_view.xml',
    ],
}
