# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mrp Multi Company",
    "summary": """
        Allows to define several different companies on mrp boms""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["mrp", "product_multi_company"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
