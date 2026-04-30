import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.base_multi_company import hooks
except ImportError:
    _logger.info("Cannot find `base_multi_company` module in addons path.")


def post_init_hook(cr, registry):
    hooks.post_init_hook(
        cr,
        "base.res_partner_rule",
        "res.partner",
    )
    # Additionally sync each user's partner.company_ids with the user's
    # allowed company_ids. The base hook only copies the legacy single
    # partner.company_id, which leaves users allowed in multiple companies
    # unable to read their own partner record (and thus unable to log in)
    # in any company beyond the one originally stored on the partner.
    cr.execute(
        """
        INSERT INTO res_company_res_partner_rel (res_partner_id, res_company_id)
        SELECT u.partner_id, rel.cid
        FROM res_users u
        JOIN res_company_users_rel rel ON rel.user_id = u.id
        WHERE u.partner_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )


def uninstall_hook(cr, registry):
    """
    Restore original domain for base.res_partner_rule

    Args:
        cr (Cursor): Database cursor to use for operation.
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
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
