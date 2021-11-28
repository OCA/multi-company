# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Company Code",
    "summary": "Add 'code' field on company model",
    "version": "14.0.1.0.1",
    "category": "Tools",
    "author": "GRAP, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": ["web"],
    "data": ["views/view_res_company.xml"],
    "demo": ["demo/res_groups.xml", "demo/res_company.xml"],
    "images": [
        "static/description/res_company_form.png",
        "static/description/res_company_tree.png",
    ],
    "installable": True,
}
