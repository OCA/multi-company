# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Multicompany Configuration",
    "summary": """
        Simplify the configuration on multicompany environments""",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "author": "CreuBlanca, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["base_sparse_field", "product"],
    "data": [
        "views/product_category.xml",
        "views/product_template.xml",
        "views/product_product.xml",
        "views/res_partner.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "multicompany_configuration/static/src/js/multicompany_data_field.js",
            "multicompany_configuration/static/src/scss/multicompany_data_field.scss",
        ],
    },
    "demo": [],
}
