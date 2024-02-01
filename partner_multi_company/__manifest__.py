# Copyright 2015 Oihane Crucelaegui
# Copyright 2015-2019 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Partner multi-company",
    "summary": "Select individually the partner visibility on each company",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "depends": ["base_multi_company", "base_setup"],
    "author": "Tecnativa, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "category": "Partner Management",
    "data": [
        "views/res_config_settings.xml",
        "views/res_partner_view.xml",
    ],
    "maintainers": [
        "aleuffre",
        "PicchiSeba",
        "renda-dev",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
