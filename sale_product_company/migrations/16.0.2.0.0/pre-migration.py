# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.table_exists(env.cr, "product_template_res_company_rel"):
        return
    openupgrade.rename_tables(
        env.cr,
        [
            (
                "product_template_res_company_rel",
                "product_template_sale_product_company_company_rel",
            )
        ],
    )
