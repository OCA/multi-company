from odoo.tools import config
from .hooks import pre_init_partner_phone

from . import models

if not config.get("without_demo"):
    from . import demo


def pre_init_hook(env):
    if not config.get("without_demo"):
        pre_init_partner_phone(env)
