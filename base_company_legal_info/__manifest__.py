# © 2014-2016 Akretion (http://www.akretion.com)
# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# @author: Quentin DUPONT (quentin.dupont@grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base - Company Legal Information",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "license": "AGPL-3",
    "summary": "Adds Legal informations on company model",
    "author": "Akretion,GRAP,Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain", "quentinDupont"],
    "website": "https://github.com/OCA/multi-company",
    "depends": [
        "web",
    ],
    "data": [
        "views/view_res_company.xml",
        "views/external_layout_footer.xml",
    ],
    "demo": [
        "demo/res_groups.xml",
        "demo/res_company.xml",
    ],
    "installable": True,
}
