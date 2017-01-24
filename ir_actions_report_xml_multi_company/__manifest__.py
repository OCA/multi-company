# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV, Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Ir Actions Report Xml Multi Company',
    'summary': """
        Make Report Actions multi-company aware""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'www.acsone.eu',
    'depends': [
        'report',
    ],
    'data': [
        'views/ir_actions_report_xml.xml',
        'security/multi_company.xml',
    ],
}
