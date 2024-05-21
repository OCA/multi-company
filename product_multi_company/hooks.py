# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.base_multi_company import hooks
except ImportError:
    _logger.info("Cannot find `base_multi_company` module in addons path.")


def post_init_hook(env):
    hooks.post_init_hook(
        env,
        "product.product_comp_rule",
        "product.template",
    )


def uninstall_hook(env):
    """Restore product rule to base value.

    Args:
        env (Environment): Environment to use for operation.
    """
    rule = env.ref("product.product_comp_rule")
    if rule:  # safeguard if it's deleted
        rule.write(
            {
                "domain_force": (
                    " ['|', ('company_id', 'parent_of', company_ids),"
                    " ('company_id', '=', False)]"
                ),
            }
        )
