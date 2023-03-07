import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        rule = env.ref("base.res_partner_rule")
        if not rule:  # safeguard if it's deleted
            return
        rule.write(
            {
                "active": True,
                "domain_force": (
                    "['|', '|',"
                    "('partner_share', '=', False),"
                    "('no_company_ids', '=', True),"
                    "('company_ids', 'in', company_ids)]"
                ),
            }
        )


def uninstall_hook(cr, registry):
    """Restore product rule to base value.

    Args:
        cr (Cursor): Database cursor to use for operation.
        rule_ref (string): XML ID of security rule to remove the
            `domain_force` from.
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Change access rule
        rule = env.ref("base.res_partner_rule")
        rule.write(
            {
                "active": False,
                "domain_force": (
                    "['|', '|', ('partner_share', '=', False), "
                    "('company_id', 'in', company_ids), "
                    "('company_id', '=', False)]"
                ),
            }
        )
