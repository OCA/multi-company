# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Pricelist Multi Company - Website Sale",
    "summary": "Glue module: pricelist company_ids sharing for Website Sale",
    "category": "Website",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": [
        "product_pricelist_multi_company",
        "website_sale",
    ],
    "data": [
        "security/product_pricelist_security.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "auto_install": True,
}
