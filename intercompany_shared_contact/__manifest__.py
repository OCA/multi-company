# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Intercompany shared contact",
    "summary": (
        "User of each company are contact of a company partner.\n"
        "All child address of a company are automatically shared"
    ),
    "version": "14.0.1.0.1",
    "category": "Partner",
    "website": "https://github.com/OCA/multi-company",
    "author": "Odoo Community Association (OCA), Akretion",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "contacts",
    ],
    "data": [
        "security/ir_rule.xml",
    ],
    "demo": [],
}
