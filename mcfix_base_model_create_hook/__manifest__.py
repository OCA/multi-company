# Copyright 2018 Creu Blanca
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': 'Multi Company Fix Base Create Hook',
    'version': '11.0.1.0.0',
    'summary': 'Hook to allow extensions to _create method in Models.py',
    'author': 'Eficent, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/multi-company',
    'license': 'LGPL-3',
    'depends': ['base'],
    'sequence': 30,
    'post_load': 'post_load_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
