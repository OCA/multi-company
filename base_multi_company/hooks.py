# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 LasLabs Inc.
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

__all__ = [
    "post_init_hook",
    "uninstall_hook",
]


def set_security_rule(env, rule_ref):
    """Set the condition for multi-company in the security rule.

    :param: env: Environment
    :param: rule_ref: XML-ID of the security rule to change.
    """
    rule = env.ref(rule_ref)
    if rule:  # safeguard if it's deleted
        rule.write(
            {
                "active": True,
                "domain_force": (
                    "['|', ('company_ids', '=', False),"
                    " ('company_ids', 'in', company_ids)]"
                ),
            }
        )


def post_init_hook(env, rule_ref, model_name):
    """Set the `domain_force` and default `company_ids` to `company_id`.

    Args:
        env (Environment): Environment to use for operation.
        rule_ref (string): XML ID of security rule to write the
            `domain_force` from.
        model_name (string): Name of Odoo model object to search for
            existing records.
    """
    set_security_rule(env, rule_ref)
    # Copy company values
    model = env[model_name]
    table_name = model._fields["company_ids"].relation
    column1 = model._fields["company_ids"].column1
    column2 = model._fields["company_ids"].column2
    SQL = f"""
        INSERT INTO {table_name}
        ({column1}, {column2})
        SELECT id, company_id FROM {model._table} WHERE company_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """
    env.cr.execute(SQL)


def uninstall_hook(env, rule_ref):
    """Restore rule to base value.

    Args:
        env (Environment): Environment to use for operation.
        rule_ref (string): XML ID of security rule to remove the
            `domain_force` from.
    """
    # Change access rule
    rule = env.ref(rule_ref)
    if rule:  # safeguard if it's deleted
        rule.write(
            {
                "active": False,
                "domain_force": (
                    " ['|', ('company_ids', '=', False),"
                    " ('company_ids', 'in', company_ids)]"
                ),
            }
        )
