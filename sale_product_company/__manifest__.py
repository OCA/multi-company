# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "sale product company",
    "summary": "Set selling companies on product",
    "version": "16.0.2.0.0",
    "development_status": "Alpha",
    "category": "Sale Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "data": [
        "views/product_template_view.xml",
        "views/sale_order_view.xml",
    ],
    "depends": [
        "sale",
        "base_view_inheritance_extension",
    ],
}
