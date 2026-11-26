# Copyright 2026 XXP LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import sql


def pre_init_hook(cr):
    """Create allow_single_company before the registry reads res.users.

    setup_models() runs after the field is loaded and before init_models().
    A company read then selects every stored column of res.users.
    """
    if not sql.column_exists(cr, "res_users", "allow_single_company"):
        sql.create_column(
            cr, "res_users", "allow_single_company", "bool", "Single Active Company"
        )
