# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "sale product company multi add",
    "summary": "Filter products by selling companies on sale order multi add",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Sale Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "data": [
        "wizard/sale_import_products_view.xml",
    ],
    "depends": [
        "sale_product_company",
        "sale_product_multi_add",
    ],
}
