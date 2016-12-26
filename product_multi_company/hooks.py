# -*- coding: utf-8 -*-
# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.base_multi_company import hooks
except ImportError:
    _logger.info('Cannot find `base_multi_company` module in addons path.')


def post_init_hook(cr, registry):
    hooks.post_init_hook(
        cr,
        'product.product_comp_rule',
        'product.template',
    )


def uninstall_hook(cr, registry):
    hooks.uninstall_hook(
        cr,
        'product.product_comp_rule',
    )
