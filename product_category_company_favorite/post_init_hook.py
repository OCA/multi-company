# Copyright (C) 2023-Today: GRAP (<http://www.grap.coop/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def initialize_is_favorite_field(env):
    for company in env["res.company"].with_context(active_test=False).search([]):
        _logger.info(f"Configure is_favorite field for the company {company.name}")
        company._configure_favorite_product_category()
