# Copyright (C) 2026 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _hook_recompute_company_qty(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    categories = env["res.company.category"].with_context(active_test=False).search([])
    _logger.info("res_company_category_active: recompute company quantity")
    categories._compute_company_qty()
