# Copyright 2019 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    "name": "Product Supplier Intercompany",
    "version": "14.0.1.0.0",
    "category": "Generic Modules/Others",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA), Akretion",
    "website": "https://github.com/akretion/ak-odoo-incubator",
    "depends": [
        "sale_management",
        "purchase_sale_inter_company",
    ],
    "data": ["views/pricelist_views.xml", "security/supplierinfo.xml"],
    "demo": ["demo/pricelist.xml"],
    "installable": True,
    "maintainers": ["PierrickBrun", "sebastienbeau", "kevinkhao"],
}
