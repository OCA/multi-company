# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Sale Note Intercompany",
    "summary": "Propagate note from purchase to sale line",
    "version": "14.0.1.0.0",
    "category": "multi-company",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["Kev-Roche"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale_order_line_note",
        "purchase_order_line_note",
        "purchase_sale_inter_company",
    ],
    "data": [],
}
