# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Category multi-company",
    "summary": "",
    "author": "ForgeFlow S.L.,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Product Management",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "base_multi_company",
        "product_category_inter_company",
        "product_multi_company",
    ],
    "data": [
        "views/product_category.xml",
    ],
}
