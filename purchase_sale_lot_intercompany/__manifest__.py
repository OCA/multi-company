# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Sale Lot Intercompany",
    "summary": "Intercompany PO/SO lot number propagation",
    "version": "14.0.1.0.0",
    "category": "CAT",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["Kev-Roche"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "purchase_lot",
        "purchase_sale_inter_company",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
}
