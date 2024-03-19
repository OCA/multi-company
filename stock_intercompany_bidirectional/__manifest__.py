# Copyright (C) 2023 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Intercompany Bidirectional",
    "summary": "Bidirectional operations for the Stock Intercomany module",
    "version": "16.0.1.0.0",
    "category": "Inventory/Inventory",
    "website": "https://github.com/OCA/multi-company",
    "author": "Cetmix, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["stock_intercompany"],
    "data": [
        "views/res_config_settings.xml",
    ],
    "demo": ["data/demo_data.xml"],
}
