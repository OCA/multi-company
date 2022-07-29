# Copyright 2022 INVITU SARL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Category Multi Company",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "INVITU SARL," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["product"],
    "post_init_hook": "post_init_hook",
    "data": ["security/product_category.xml", "views/product_views.xml"],
}
