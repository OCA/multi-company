# Copyright 2013-2014 Odoo SA
# Copyright 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Inter Company Invoices",
    "summary": "Intercompany invoice rules",
    "version": "16.0.1.1.1",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/multi-company",
    "author": "Odoo SA, Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["account", "base_setup"],
    "data": [
        "views/account_move_views.xml",
        "views/res_config_settings_view.xml",
    ],
    "demo": [
        "demo/inter_company_demo.xml",
    ],
    "installable": True,
}
