# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui
# © 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Partner multi-company",
    "summary": "Select individually the partner visibility on each company",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "base_multi_company",
        "base_suspend_security",
    ],
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "category": "Partner Management",
    "data": [
        "views/res_partner_view.xml",
    ],
    "installable": True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
