# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Pricelist Item Multi Attribute Value Intercompany",
    "summary": "Product Pricelist Item Multi Attribute Value Intercompany",
    "version": "16.0.1.0.0",
    "category": "Generic Modules/Others",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": ["Kev-Roche"],
    "application": False,
    "installable": True,
    "depends": [
        "product_pricelist_item_multi_attribute_value",
        "product_supplierinfo_intercompany",
    ],
    "data": [
        "views/product_supplierinfo.xml",
    ],
}
