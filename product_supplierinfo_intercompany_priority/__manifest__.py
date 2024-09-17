# Copyright 2024 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Supplierinfo Intercompany priority",
    "summary": "Intercompany",
    "version": "16.0.1.0.0",
    "category": "Purchase Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": ["Kev-Roche"],
    "application": False,
    "installable": True,
    "depends": [
        "product_supplierinfo_intercompany",
        "purchase_sale_stock_inter_company",
    ],
    "data": [
        "views/res_config.xml",
    ],
}
