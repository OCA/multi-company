# Copyright 2023 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{
    "name": "Product Packaging Container Deposit Purchase to Sale Order inter-company",
    "summary": """
    Add compatibility between OCA product_packaging_container_deposit and
    purchase_sale_inter_company""",
    "version": "16.0.1.0.0",
    "category": "Purchase Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "purchase_sale_inter_company",
        "sale_product_packaging_container_deposit",
        "purchase_product_packaging_container_deposit",
    ],
}
