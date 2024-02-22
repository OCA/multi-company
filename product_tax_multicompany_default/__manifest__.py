# Copyright 2017-2019 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Tax Multi Company Default",
    "version": "14.0.1.2.0",
    "category": "Account",
    "website": "https://github.com/OCA/multi-company",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["account", "product", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/account_tax_company_map_views.xml",
        "views/account_tax_views.xml",
        "views/product_template_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [
        "demo/account_tax_demo.xml",
        "demo/account_tax_company_map_demo.xml",
    ],
    "maintainers": ["Shide"],
}
