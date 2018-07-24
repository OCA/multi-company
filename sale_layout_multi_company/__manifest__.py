# -*- coding: utf-8 -*-
# Copyright 2016 Lorenzo Battistini - Agile Business Group
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Layout - Multi company",
    "summary": "Multi company features for sale_layout",
    "version": "10.0.1.0.0",
    "category": "Sales Management",
    "website": "https://github.com/OCA/multi-company/tree/10.0/"
               "sale_layout_multi_company",
    "author": "Agile Business Group, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base_multi_company",
        "sale"
    ],
    "data": [
        "views/sale_layout_view.xml",
        "security/record_rules.xml",
    ],
}
