# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def fill_account_move_auto_invoice_id(env):
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE account_move am
            SET
                auto_generated = ai.auto_generated,
                auto_invoice_id = am2.id
            FROM account_invoice ai
                JOIN account_invoice ai2 ON ai.auto_invoice_id = ai2.id
                JOIN account_move am2 ON am2.old_invoice_id = ai2.id
            WHERE am.old_invoice_id = ai.id AND ai.auto_invoice_id IS NOT NULL
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    fill_account_move_auto_invoice_id(env)
