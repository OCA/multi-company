# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Sale Stock Inter Company Transit Receipt",
    "summary": "Receive inter-company purchases through the incoming transit",
    "version": "18.0.1.0.0",
    "category": "Purchase Management",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": [
        "purchase_sale_stock_inter_company",
        "purchase_stock_transit_receipt",
    ],
    "data": ["views/res_config_settings_views.xml"],
    "installable": True,
    "auto_install": True,
}
