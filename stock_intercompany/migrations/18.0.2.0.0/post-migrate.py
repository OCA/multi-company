# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_fields(
        env,
        [
            (
                "stock.picking",
                "stock_picking",
                "counterpart_of_picking_id",
                "intercompany_parent_id",
            ),
            (
                "stock.move",
                "stock_move",
                "counterpart_of_move_id",
                "intercompany_origin_move_id",
            ),
            (
                "stock.move.line",
                "stock_move_line",
                "counterpart_of_line_id",
                "intercompany_origin_line_id",
            ),
        ],
    )
