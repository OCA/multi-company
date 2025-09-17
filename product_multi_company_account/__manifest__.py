# Copyright 2025 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Product multi-company Account",
    "summary": "Fixes tax access issues in product multi-company "
    "for accounting integration",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Product Management",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["product_multi_company", "account"],
    "data": [
        "security/ir_rule.xml",
    ],
    "auto_install": True,
    "installable": True,
}
