# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.base_multi_company import hooks
except ImportError:
    _logger.info("Cannot find `base_multi_company` module in addons path.")


def post_init_hook(env):
    hooks.fill_company_ids(env, "event.event")
