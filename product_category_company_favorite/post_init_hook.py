# Copyright (C) 2023-Today: GRAP (<http://www.grap.coop/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def initialize_is_favorite_field(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env["res.company"].with_context(active_test=False).search([]):
        _logger.info("Configure is_favorite field for the company %s" % (company.name))
        company._configure_favorite_product_category()
