from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    rule_ids = env["ir.rule"].search(
        [
            (
                "domain_force",
                "=",
                (
                    "['|', ('no_company_ids', '=', True), ('company_ids', "
                    "'in', company_ids)]"
                ),
            )
        ]
    )

    rule_ids.write(
        {
            "domain_force": (
                "['|', ('company_ids', '=', False), ('company_ids', "
                "'in', company_ids)]"
            )
        }
    )
