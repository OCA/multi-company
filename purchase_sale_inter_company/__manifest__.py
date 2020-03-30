# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Inter Company Module for Purchase to Sale Order",
    "summary": "Intercompany PO/SO rules",
    "version": "13.0.1.0.0",
    "category": "Purchase Management",
    "website": "http://www.github.com/OCA/multi-company",
    "author": "Odoo SA, Akretion, Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["sale", "purchase", "stock", "account_invoice_inter_company"],
    "data": ["views/res_config_view.xml"],
}
