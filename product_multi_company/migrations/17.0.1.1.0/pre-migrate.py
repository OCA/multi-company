# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)
from logging import getLogger

from openupgradelib import openupgrade

from odoo.tools import safe_eval

_logger = getLogger(__name__)


PREVIOUS_DOMAIN = [
    "|",
    ("company_ids", "in", "COMPANY_IDS"),
    ("company_ids", "=", False),
]


UPSTREAM_DOMAIN = " [('company_id', 'in', company_ids + [False])]"


@openupgrade.migrate()
def migrate(env, version):
    """Restore upstream partner rule."""
    rule = env.ref("product.product_comp_rule", False)

    if not rule:
        return

    try:
        domain = safe_eval(
            rule.domain_force, locals_dict={"company_ids": "COMPANY_IDS"}
        )

    except Exception:
        _logger.warning("Unable to evaluate domain_force")

        return

    if domain == PREVIOUS_DOMAIN:
        rule.domain_force = UPSTREAM_DOMAIN

        _logger.info("Restored upstream partner rule")
