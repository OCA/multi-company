# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Project - Multi Company",
    "summary": """
        This module adds support for multi company on Project Module.""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "GRAP, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/multi-company",
    "installable": True,
    "depends": ["project"],
    "data": [
        "security/ir_rule.xml",
        "views/view_project_tags.xml",
        "views/view_project_task_type.xml",
    ],
}
