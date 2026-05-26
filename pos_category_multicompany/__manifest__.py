# Copyright (C) 2013 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# @author Julien WESTE
# @author Quentin DUPONT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Point Of Sale Category Multi Company",
    "summary": "Point of Sale Category in Multi company context",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "GRAP, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain", "quentinDupont"],
    "website": "https://github.com/OCA/multi-company",
    "depends": [
        "point_of_sale",
    ],
    "data": [
        "security/ir_rule.xml",
        "views/view_pos_category.xml",
    ],
    "demo": [
        "demo/res_groups.xml",
    ],
    "images": [
        "static/description/pos_category_tree.png",
    ],
    "installable": True,
}
