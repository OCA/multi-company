# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Multi Company Fix Base Create Hook',
    'version': '11.0.1.0.0',
    'summary': 'Hook to allow extensions to _create method in Models.py',
    'author': 'Eficent, Odoo Community Association (OCA)',
    'website': 'http://www.eficent.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'sequence': 30,
    'post_load': 'post_load_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
