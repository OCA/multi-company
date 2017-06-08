# -*- coding: utf-8 -*-
#############################################################################
# (c) 2015 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#############################################################################

{
    "name": "Stock Production Lot Multi Company",
    "summary": "Make serial numbers multi-company aware",
    "version": "10.0.1.0.0",
    "category": "Stock",
    "license": "AGPL-3",
    "author": "OdooMRP team, "
              "AvanzOSC, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Odoo Community Association (OCA)",
    "depends": [
        "base_multi_company",
        "stock",
    ],
    "data": [
        "security/stock_production_lot_security.xml",
        "views/stock_production_lot_view.xml",
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
}
