# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'User-defined Export List Multi Company',
    'summary': """
        This module add multi-company management to user-defined export list.
        """,
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/multi-company',
    'depends': ['base'],
    'data': ['security/ir_exports.xml'],
    "post_init_hook": "post_init_hook",
}
