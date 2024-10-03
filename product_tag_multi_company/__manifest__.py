# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Tag Multi Company",
    "summary": "This module add multi-company management to product tag",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "Product Management",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["product"],
    "data": [
        "security/ir_rules.xml",
        "views/product_tag_views.xml",
        "views/product_views.xml",
    ],
}
