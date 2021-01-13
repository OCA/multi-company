# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Intercompany shared contact",
    "summary": (
        "User of each company are contact of a company partner.\n"
        "All child address of a company are automatically shared"
    ),
    "version": "14.0.1.0.0",
    "category": "Partner",
    "website": "https://github.com/akretion/ak-odoo-incubator",
    "author": " Akretion",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "base",
        "security_rule_not_editable",  # optional for updating rule automatically
    ],
    "data": [
        "views/res_users_view.xml",
        "security/ir_rule.xml",
    ],
    "demo": [],
}
