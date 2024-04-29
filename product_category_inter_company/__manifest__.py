# Copyright 2022 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Category Inter Company",
    "summary": "Product categories as company dependent",
    "version": "15.0.1.1.0",
    "category": "Product",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "product",
    ],
    "data": [
        "views/product_category.xml",
        "views/product_template_view.xml",
        "security/ir_rule.xml",
    ],
}
