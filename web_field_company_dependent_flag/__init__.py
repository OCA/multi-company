from odoo.tools import config
from .hooks import pre_init_hook

from . import models

if not config.get("without_demo"):
    from . import demo
