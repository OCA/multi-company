from . import models


def post_init_hook(env):
    """We should not set the company by default on all existing mail templates
    when installing this module, as many standard templates do not need to
    be company-specific.
    Since Odoo 16.0, the default `company_id` on new mail templates has been `False`,
    which aligns with this behavior. However, when users create new templates,
    it is still reasonable to default to the current company if applicable."""
    env.cr.execute("UPDATE mail_template SET company_id=null")
