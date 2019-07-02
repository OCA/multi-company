# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Calendar Event Multi Company',
    'summary': """
        This module add multi-company management to calendar events""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/multi-company',
    'depends': ['calendar'],
    'data': [
        'security/calendar_event.xml',
        'views/calendar_event.xml',
    ],
}
