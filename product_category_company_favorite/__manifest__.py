# Copyright (C) 2023 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Product Categories - Company Favorites",
    "summary": "Possilibity to set favorite product categories per company",
    "version": "16.0.1.0.1",
    "category": "Product",
    "author": "GRAP,Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": ["product"],
    "excludes": ["product_category_company"],
    "data": ["views/view_product_category.xml"],
    "demo": ["demo/res_company.xml"],
    "images": ["static/description/product_category_tree.png"],
    "installable": True,
    "post_init_hook": "initialize_is_favorite_field",
}
