# Copyright (C) 2024 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _logger.info(
        "Give access to all the child companies for users"
        " that have access to parent companies."
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    users = env["res.users"].search([])
    users._propagate_access_to_child_companies()
