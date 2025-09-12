# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License LGPL-3.0 - http://www.gnu.org/licenses/lgpl.html

{
    "name": "Product multi-company",
    "summary": "Select individually the product template visibility on each " "company",
    "author": "Tecnativa," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Product Management",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "depends": ["base_multi_company", "product"],
    "data": ["views/product_template_view.xml"],
    "post_init_hook": "post_init_hook",
}
