# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Intercompany Pricelist",
    "summary": "Auto-sync vendor supplierinfo from inter-company pricelists",
    "category": "Product",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": ["tobiaszehntner"],
    "website": "https://github.com/OCA/multi-company",
    "depends": [
        "product",
    ],
    "data": [
        "views/product_pricelist_views.xml",
        "views/product_supplierinfo_views.xml",
    ],
}
