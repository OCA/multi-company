# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Pricelist Multi Company",
    "summary": "Pricelists shared between Companies",
    "category": "Product",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": [
        "product",
    ],
    "data": [
        "security/product_pricelist_security.xml",
        "views/product_pricelist_views.xml",
    ],
    "uninstall_hook": "uninstall_hook",
}
