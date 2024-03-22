# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Inter Company Module for Purchase to Sale Order",
    "summary": "Intercompany PO/SO rules",
    "version": "14.0.2.1.2",
    "category": "Purchase Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Odoo SA, Akretion, Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["aleuffre", "renda-dev"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "sale_stock",
        "purchase_stock",
        "account_invoice_inter_company",
    ],
    "data": [
        "views/res_config_view.xml",
        "wizard/stock_backorder_confirmation_views.xml",
    ],
    "demo": [
        "demo/res_partner_demo.xml",
    ],
}
