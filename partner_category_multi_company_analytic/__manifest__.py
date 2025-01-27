# Copyright 2025 ForgeFlow (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Partner Category Multi Company Analytic",
    "summary": """
        Multi-company check in Partner categories""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["analytic", "partner_category_multi_company"],
    "data": [
        "views/analytic_distribution_model_views.xml",
    ],
    "auto_install": True,
}
