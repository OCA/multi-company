# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Company Representative",
    "summary": "Manage company representatives and their roles",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "NICO SOLUTIONS - ENGINEERING & IT, Odoo Community Association (OCA)",
    "maintainers": ["NICO-SOLUTIONS"],
    "website": "https://github.com/OCA/multi-company",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/res_company_views.xml",
        "views/res_company_representative_views.xml",
        "views/res_company_representative_role_views.xml",
    ],
}
