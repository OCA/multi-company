# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Supplierinfo Mandatory Intercompany",
    "summary": "Check if a intercompany supplierinfo exist before confirming a purchase order",
    "version": "14.0.1.0.0",
    "category": "Generic Modules/Others",
    "author": "Odoo Community Association (OCA), Akretion",
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "maintainers": ["Kev-Roche"],
    "application": False,
    "installable": True,
    "depends": [
        "product_supplierinfo_intercompany",
    ],
    "data": [
        "views/purchase_order.xml",
    ],
}
