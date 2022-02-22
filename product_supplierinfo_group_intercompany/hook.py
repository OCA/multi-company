# Copyright 2022 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def split_supplierinfo_groups_by_pricelist(env, version):
    """
    if the modules:
        * product_supplierinfo_group
        * product_supplier_intercompany
    were used independently before installing this module,
    we need to ensure supplierinfo groups are split by pricelist
    """

    def _reset_supplierinfo_group(supplierinfo_item):
        vals = {}
        for key in env["product.supplierinfo"]._fields_for_group_match().keys():
            vals[key] = getattr(supplierinfo_item, key)
        env["product.supplierinfo"]._set_group_id(vals)
        supplierinfo_item.write(vals)

    has_intercompany_pricelist = env["product.supplierinfo"].search(
        [("intercompany_pricelist_id", "!=", False)]
    )
    supplierinfo_groups = has_intercompany_pricelist.supplierinfo_group_id
    for group in supplierinfo_groups:
        if len(group.supplierinfo_ids.intercompany_pricelist_id.ids) != 1:
            for item in group.supplierinfo_ids:
                _reset_supplierinfo_group(item)
