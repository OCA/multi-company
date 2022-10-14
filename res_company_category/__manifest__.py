# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Company Categories",
    "version": "16.0.1.0.1",
    "category": "Tools",
    "author": "GRAP, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": [
        "base",
        "res_company_search_view",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/view_res_company.xml",
        "views/view_res_company_category.xml",
    ],
    "demo": [
        "demo/res_groups.xml",
        "demo/res_company_category.xml",
        "demo/res_company.xml",
    ],
    "installable": True,
}
