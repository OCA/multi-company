# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Invoice Product Company Check",
    "summary": """Check company's product
            before to set him a specific company""",
    "version": "14.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["Kev-Roche"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
        "base_company_check",
    ],
}
