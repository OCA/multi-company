# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "User-defined Filters Multi Company",
    "summary": """
        This module add multi-company management to user-defined filters""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["base"],
    "data": ["security/ir_filters.xml", "views/ir_filters.xml"],
    "post_init_hook": "post_init_hook",
}
