# coding: utf-8
# Copyright 2019 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    "name": "Product Supplier Intercompany",
    "version": "10.0.0.0.0",
    "category": "Generic Modules/Others",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/multi-company",
    "depends": ["sale"],
    "data": ["views/pricelist_views.xml", "security/supplierinfo.xml"],
    "demo": ["demo/pricelist.xml"],
    "installable": True,
}
