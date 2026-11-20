# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Crm Lost Reason Multi Company",
    "summary": "This module add multi-company management to crm lost reason",
    "version": "20.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["crm"],
    "data": [
        "security/ir.access.csv",
        "views/crm_lost_reason.xml",
    ],
}
