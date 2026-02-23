# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Inter Company Module for RMA",
    "version": "18.0.1.0.0",
    "category": "Purchase Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["purchase_sale_stock_inter_company", "rma_sale", "stock_dropshipping"],
    "data": [
        "views/rma_views.xml",
    ],
    "maintainers": ["victoralmau"],
}
