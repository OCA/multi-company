# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "sale stock warehouse multicompany",
    "summary": "Allow multiple companies to sell the stock of a shared warehouse",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery"],
    "data": [
        "views/stock_warehouse_views.xml",
        "views/stock_route_views.xml",
    ],
}
