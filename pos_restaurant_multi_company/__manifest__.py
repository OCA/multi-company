# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PoS Restaurant - Multi Company",
    "summary": """
        This module adds support for multi company on PoS Restaurant.""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "GRAP, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/multi-company",
    "installable": True,
    "depends": ["pos_restaurant"],
    "data": [
        "security/ir_rule.xml",
        "views/restaurant_floor.xml",
        "views/restaurant_printer.xml",
    ],
    "post_init_hook": "post_init_hook",
}
