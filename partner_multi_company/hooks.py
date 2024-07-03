import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    Set access rule to support multi-company fields
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Change access rule
    rule = env.ref("base.res_partner_rule")
    rule.write(
        {
            "domain_force": (
                "['|', '|', ('partner_share', '=', False),"
                "('company_ids', 'in', company_ids),"
                "('company_ids', '=', False)]"
            ),
        }
    )
    # Initialize m2m table for preserving old restrictions
    cr.execute(
        """
        INSERT INTO res_company_res_partner_rel
        (res_partner_id, res_company_id)
        SELECT id, company_id
        FROM res_partner
        WHERE company_id IS NOT NULL
        """
    )


def uninstall_hook(cr, registry):
    """Restore product rule to base value.

    Args:
        cr (Cursor): Database cursor to use for operation.
        rule_ref (string): XML ID of security rule to remove the
            `domain_force` from.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Change access rule
    rule = env.ref("base.res_partner_rule")
    rule.write(
        {
            "domain_force": (
                "['|', '|', ('partner_share', '=', False),"
                "('company_id', 'in', company_ids),"
                "('company_id', '=', False)]"
            ),
        }
    )
