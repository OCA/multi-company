# Copyright (C) 2026 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Active Company Categories",
    "summary": "glue module between Company categories and active Companies",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "author": "GRAP, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": ["res_company_active", "res_company_category"],
    "post_init_hook": "_hook_recompute_company_qty",
    "installable": True,
    "auto_install": True,
}
