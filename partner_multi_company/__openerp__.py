# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Partner multi-company",
    "summary": "Select individually the partner visibility on each company",
    "version": "8.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base"],
    "author": "Odoo Community Association (OCA)",
    "contributors": [
        "Oihane Crucelaegui <oihanecruce@avanzosc.es>",
    ],
    "category": "Custom Module",
    "data": [
        "views/res_partner_view.xml",
    ],
    "installable": True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
