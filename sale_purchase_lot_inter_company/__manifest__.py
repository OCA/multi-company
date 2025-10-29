# Copyright (c) 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# @author Guillaume MASSON <guillaume.masson@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Purchase Lot Intercompany",
    "summary": "Intercompany SO/PO lot number propagation",
    "version": "16.0.1.0.0",
    "category": "Sale Management",
    "website": "https://github.com/OCA/multi-company",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["metaminux"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale_order_lot_selection",
        "purchase_lot",
        "sale_purchase_stock_inter_company",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
}
