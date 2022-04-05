# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tools.sql import column_exists


def migrate(cr, version):
    if not column_exists(cr, "account_move", "old_invoice_id"):
        # detect if coming from v13 migrating with OpenUpgrade
        return
    cr.execute(
        """
        UPDATE account_move am
        SET consolidated_by_id = ai.consolidated_by_id
        FROM account_invoice ai
        WHERE am.old_invoice_id = ai.id AND ai.consolidated_by_id IS NOT NULL
        """
    )
    cr.execute(
        """
        UPDATE account_move_line aml
        SET consolidated_by_id = ail.consolidated_by_id
        FROM account_invoice_line ail
        WHERE aml.old_invoice_line_id = ail.id AND ail.consolidated_by_id IS NOT NULL
        """
    )
    cr.execute(
        """
        UPDATE account_invoice_consolidated aic
        SET invoice_id = am.id
        FROM account_move am
        WHERE aic.invoice_id = am.old_invoice_id
        """
    )
