# Copyright 2022 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {"automatic_intercompany_sync": True})
    suppliers = env["product.supplierinfo"].search(
        [
            ("group_id.intercompany_pricelist_id", "!=", False),
            ("intercompany_pricelist_id", "=", False),
        ]
    )
    for supplier in suppliers:
        variant = supplier.product_id
        template = supplier.product_tmpl_id
        pricelist = supplier.group_id.intercompany_pricelist_id
        supplier.unlink()
        if variant:
            variant._synchronise_supplier_info(pricelist)
        else:
            template._synchronise_supplier_info(pricelist)
