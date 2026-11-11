# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Partner Multi Company Field Visible",
    "summary": "Show the own-company field on contacts to non multi-company users",
    "version": "19.0.1.0.0",
    "author": "Canarias Conectada, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Partner Management",
    "license": "AGPL-3",
    "depends": ["base_setup", "multi_company_field_visible", "partner_multi_company"],
    "data": [
        "views/res_partner_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "auto_install": True,
    "installable": True,
}
