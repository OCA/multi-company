# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Product Multi Company Field Visible",
    "summary": "Show the own-company field on products to non multi-company users",
    "version": "19.0.1.0.0",
    "author": "Canarias Conectada, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Product Management",
    "license": "AGPL-3",
    "depends": ["base_setup", "multi_company_field_visible", "product_multi_company"],
    "data": [
        "views/product_template_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "auto_install": True,
    "installable": True,
}
