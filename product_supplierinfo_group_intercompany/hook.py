# Copyright 2022 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """
    if the modules:
        * product_supplierinfo_group
        * product_supplierinfo_intercompany
    were used independently before installing this module,
    we need to ensure supplierinfo groups are split by pricelist
    """
    env = api.Environment(cr, SUPERUSER_ID, {"automatic_intercompany_sync": True})
    matching_keys = env["product.supplierinfo"]._fields_for_group_match().keys()

    supplierinfos = env["product.supplierinfo"].search(
        [("intercompany_pricelist_id", "!=", False)]
    )
    for group in supplierinfos.group_id:
        pricelists = group.supplierinfo_ids.intercompany_pricelist_id
        if len(pricelists) == 1:
            group.intercompany_pricelist_id = pricelists
        else:
            group.intercompany_pricelist_id = pricelists[0]
            for item in group.supplierinfo_ids:
                vals = {
                    key: item._fields[key].convert_to_cache(item[key], item)
                    for key in matching_keys
                }
                new_group = env["product.supplierinfo"]._get_or_create_group(vals)
                if new_group != group:
                    item.group_id = new_group
        group._sync_sequence()
