# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def uninstall_hook(env):
    for xmlid in (
        "product.product_pricelist_comp_rule",
        "product.product_pricelist_item_comp_rule",
    ):
        env.ref(xmlid).active = True
