# Copyright (C) 2014 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# @author: Quentin DUPONT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Product Default Code with Company Code",
    "summary": "Generate product default code based on sequence"
    " defined by company, prefixed by company code",
    "version": "16.0.1.0.0",
    "category": "Product",
    "author": "GRAP, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": [
        "product",
        "res_company_code",
    ],
    "excludes": ["product_variant_default_code"],
    "data": ["views/view_product_product.xml", "views/view_product_template.xml"],
    "post_init_hook": "_create_company_sequence",
    "installable": True,
}
