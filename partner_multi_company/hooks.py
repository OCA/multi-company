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
    fix_user_partner_companies(cr)


def fix_user_partner_companies(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for user in env["res.users"].search([]):
        user_company_ids = set(user.company_ids.ids)
        partner_company_ids = set(user.partner_id.company_ids.ids)
        if not user_company_ids.issubset(partner_company_ids) and partner_company_ids:
            missing_company_ids = list(user_company_ids - partner_company_ids)
            user.partner_id.write(
                {"company_ids": [(4, company_id) for company_id in missing_company_ids]}
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
            "active": False,
            "domain_force": (
                "['|','|',('company_id.child_ids','child_of',"
                "[user.company_id.id]),('company_id','child_of',"
                "[user.company_id.id]),('company_id','=',False)]"
            ),
        }
    )
