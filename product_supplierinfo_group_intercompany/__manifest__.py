# Copyright 2022 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Supplierinfo Group Intercompany Sequence",
    "summary": """
        Add sequence field on grouped pricelist items""",
    "version": "14.0.1.1.3",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["product_supplierinfo_intercompany", "product_supplierinfo_group"],
    "data": [
        "security/ir_rule.xml",
        "views/product_supplierinfo_group.xml",
        "views/product_pricelist.xml",
    ],
    "demo": [],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
}
