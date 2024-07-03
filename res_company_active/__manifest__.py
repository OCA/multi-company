# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Company Active",
    "summary": "Add the 'active' feature on company model",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "author": "GRAP, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": [
        "base",
    ],
    "data": [
        "views/view_res_company.xml",
    ],
    "demo": [
        "demo/res_groups.xml",
        "demo/res_company.xml",
    ],
    "installable": True,
    "images": [
        "static/description/res_company_form.png",
    ],
}
