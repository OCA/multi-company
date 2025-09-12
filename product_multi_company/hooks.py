# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License LGPL-3.0 - http://www.gnu.org/licenses/lgpl.html

import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.base_multi_company import hooks
except ImportError:
    _logger.info("Cannot find `base_multi_company` module in addons path.")


def post_init_hook(env):
    hooks.fill_company_ids(
        env,
        "product.template",
    )
