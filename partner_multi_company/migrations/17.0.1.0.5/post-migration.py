# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    rule_partner_bank = env.ref("base.res_partner_bank_rule", raise_if_not_found=False)
    if rule_partner_bank:
        rule_partner_bank.write(
            {
                "domain_force": (
                    "['|', ('company_ids', 'in', company_ids),"
                    "('company_ids', '=', False)]"
                ),
            }
        )
