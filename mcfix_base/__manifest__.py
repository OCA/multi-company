# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Multi Company Fix Base',
    'version': '11.0.1.0.0',
    'summary': 'Base fixes',
    'author': 'Eficent, Odoo Community Association (OCA)',
    'website': 'http://www.eficent.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mcfix_base_model_create_hook'],
    'data': [
        'security/base_security.xml',
    ],
    'demo': [
        'data/res_partner_demo.xml',
    ],
    'sequence': 30,
    'installable': True,
    'application': False,
    'auto_install': False,
}
