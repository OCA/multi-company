# Copyright 2023 ForgeFlow <http://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Fill Is Inter Company PO field.")
    cr.execute(
        """
        WITH query AS (
            SELECT po.id AS id
            FROM purchase_order po
            JOIN sale_order so ON so.auto_purchase_order_id = po.id
        )
        UPDATE purchase_order po
        SET is_intercompany_po = true
        FROM query
        WHERE po.id = query.id;
    """
    )
    _logger.info("Fill Is Inter Company SO field.")
    cr.execute(
        """
        WITH query AS (
            SELECT so.id AS id
            FROM sale_order so
            WHERE so.auto_purchase_order_id IS NOT NULL
        )
        UPDATE sale_order so
        SET is_intercompany_so = true
        FROM query
        WHERE so.id = query.id;
    """
    )
    _logger.info("Fill Is Inter Company Transfer field.")
    cr.execute(
        """
        WITH query AS (
            SELECT sp.id AS id
            FROM stock_picking sp
            JOIN sale_order so ON sp.sale_id = so.id
            JOIN purchase_order po ON so.auto_purchase_order_id = po.id
            UNION
            SELECT sp.id AS id
            FROM sale_order so
            JOIN purchase_order po ON so.auto_purchase_order_id = po.id
            JOIN purchase_order_line pol ON pol.order_id = po.id
            JOIN stock_move sm ON sm.purchase_line_id = pol.id
            JOIN stock_picking sp ON sm.picking_id = sp.id
        )
        UPDATE stock_picking sp
        SET is_intercompany_picking = true
        FROM query
        WHERE sp.id = query.id;
    """
    )
