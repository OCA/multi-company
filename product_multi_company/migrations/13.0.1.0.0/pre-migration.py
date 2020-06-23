# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

from odoo.addons.base_multi_company import hooks


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.table_exists(env.cr, "product_template_res_company_assignment_rel"):
        openupgrade.rename_tables(
            env.cr,
            [
                (
                    "product_template_res_company_assignment_rel",
                    "product_template_res_company_rel",
                ),
            ],
        )
        openupgrade.rename_columns(
            env.cr,
            {
                "product_template_res_company_rel": [
                    ("res_company_assignment_id", "res_company_id"),
                ],
            },
        )
    hooks.set_security_rule(env, "product.product_comp_rule")
    env.ref("stock.product_pulled_flow_comp_rule").write(
        {
            "domain_force": (
                "['|', ('company_id', '=', False), ('company_id', "
                "'in', company_ids)]"
            ),
        }
    )
    env.ref("stock.stock_location_route_comp_rule").write(
        {
            "domain_force": (
                "['|', ('company_id', '=', False), ('company_id', "
                "'in', company_ids)]"
            ),
        }
    )
