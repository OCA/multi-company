# Copyright 2023 ForgeFlow <http://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _pre_create_columns(env):
    _logger.info("Pre-creating columns to avoid compute")
    if not openupgrade.column_exists(env.cr, "purchase_order", "is_intercompany_po"):
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE purchase_order
            ADD COLUMN is_intercompany_po BOOLEAN;
            COMMENT ON COLUMN purchase_order.is_intercompany_po
            IS 'Is Inter Company PO?';
            """,
        )
    if not openupgrade.column_exists(env.cr, "sale_order", "is_intercompany_so"):
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE sale_order
            ADD COLUMN is_intercompany_so BOOLEAN;
            COMMENT ON COLUMN sale_order.is_intercompany_so
            IS 'Is Inter Company SO?';
            """,
        )


@openupgrade.migrate()
def migrate(env, version):
    _pre_create_columns(env)
