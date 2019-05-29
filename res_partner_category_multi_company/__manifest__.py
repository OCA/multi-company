# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Partner Category Multi Company',
    'summary': """
        This module add multi-company management to partner categories""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/multi-company',
    'depends': ['base'],
    'data': [
        'security/res_partner_category.xml',
        'views/res_partner_category.xml',
    ],
}
