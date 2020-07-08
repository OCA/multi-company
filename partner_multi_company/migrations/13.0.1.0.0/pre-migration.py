# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

from odoo.addons.base_multi_company import hooks


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.table_exists(env.cr, "res_company_assignment_res_partner_rel"):
        openupgrade.rename_tables(
            env.cr,
            [
                (
                    "res_company_assignment_res_partner_rel",
                    "res_company_res_partner_rel",
                ),
            ],
        )
        openupgrade.rename_columns(
            env.cr,
            {
                "res_company_res_partner_rel": [
                    ("res_company_assignment_id", "res_company_id"),
                ],
            },
        )
        hooks.set_security_rule(env, "base.res_partner_rule")
