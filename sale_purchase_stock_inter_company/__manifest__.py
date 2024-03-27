# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Inter Company Module for Sale to Purchase Order with warehouse",
    "summary": "Intercompany SO/PO rules with warehouse",
    "version": "16.0.1.0.0",
    "category": "Sale Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "auto_install": True,
    "depends": ["sale_purchase_inter_company", "sale_stock", "purchase_stock"],
    "data": ["views/res_config_view.xml"],
}
