import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Set access rule to support multi-company fields
    """
    # Initialize m2m table for preserving old restrictions
    env.cr.execute("""
        INSERT INTO res_company_res_partner_rel
        (res_partner_id, res_company_id)
        SELECT id, company_id
        FROM res_partner
        WHERE company_id IS NOT NULL
        """)
    fix_user_partner_companies(env)


def fix_user_partner_companies(env):
    for user in env["res.users"].search([]):
        user_company_ids = set(user.company_ids.ids)
        partner_company_ids = set(user.partner_id.company_ids.ids)
        if not user_company_ids.issubset(partner_company_ids) and partner_company_ids:
            missing_company_ids = list(user_company_ids - partner_company_ids)
            user.partner_id.write(
                {"company_ids": [(4, company_id) for company_id in missing_company_ids]}
            )


def uninstall_hook(env):
    pass
