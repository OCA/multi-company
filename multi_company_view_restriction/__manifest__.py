# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Multicompany View Restriction",
    "summary": "View Restriction if several companies are active",
    "version": "16.0.1.0.0",
    "category": "Security",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": ["Kev-Roche"],
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "views/multicompany_view_restriction.xml",
        "security/ir.model.access.csv",
    ],
}
