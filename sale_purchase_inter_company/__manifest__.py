# Copyright 2025 Batista10
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Batista10 - Inter Company Module for Sale to Purchase Order",
    "summary": "Intercompany SO/PO rules",
    "version": "17.0.1.0.2",
    "category": "Sales Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Batista10, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "depends": ["sale_management", "sale", "purchase", "account_invoice_inter_company"],
    "data": ["views/res_config_view.xml"],
}
