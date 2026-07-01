# Copyright 2026 Canarias Conectada
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Partner Multi Company Restrict",
    "summary": "Restrict cross-company visibility of contacts linked to internal users",
    "version": "19.0.1.0.0",
    "author": "Canarias Conectada, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Partner Management",
    "license": "AGPL-3",
    "depends": ["base_setup", "partner_multi_company"],
    "data": [
        "security/res_partner_security.xml",
        "views/res_config_settings_view.xml",
    ],
    "installable": True,
}
