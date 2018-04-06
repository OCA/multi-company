# Copyright 2018 Creu Blanca
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'Multi Company Fix Base',
    'version': '11.0.1.0.0',
    'summary': 'Base fixes',
    'author': 'Eficent, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/multi-company',
    'license': 'LGPL-3',
    'depends': ['base', 'mcfix_base_model_create_hook'],
    'data': [
        'security/base_security.xml',
    ],
    'demo': [
        'demo/res_partner_demo.xml',
    ],
    'sequence': 30,
    'installable': True,
    'application': False,
    'auto_install': False,
}
