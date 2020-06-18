# Copyright 2013-2014 Odoo SA
# Copyright 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Inter Company Invoices",
    "summary": "Intercompany invoice rules",
    "version": "13.0.2.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/multi-company",
    "author": "Odoo SA, Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": ["views/account_move_views.xml", "views/res_config_settings_view.xml"],
    "installable": True,
}
