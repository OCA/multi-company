# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Order Line Display Supplier Stock",
    "summary": "Display the supplier stock on purchase order lines "
    "for intercompany purchases",
    "version": "18.0.1.0.0",
    "category": "multi-company",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": ["Kev-Roche"],
    "application": False,
    "installable": True,
    "depends": [
        "purchase",
        "sale_order_line_display_stock_per_warehouse",
    ],
    "data": [
        "views/purchase_order_line.xml",
    ],
}
