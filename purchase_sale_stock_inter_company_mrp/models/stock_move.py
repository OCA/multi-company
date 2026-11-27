# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

# The moves passed to _compute_kit_quantities are the moves of the sale
# picking: only the cancelled ones are excluded, nothing to subtract.
KIT_QUANTITIES_FILTERS = {
    "incoming_moves": lambda m: m.state != "cancel",
    "outgoing_moves": lambda m: False,
}
DELIVERED_QUANTITIES_FILTERS = {
    "incoming_moves": lambda m: m._is_outgoing()
    and (not m.origin_returned_move_id or m.to_refund),
    "outgoing_moves": lambda m: m._is_incoming() and m.to_refund,
}
RECEIVED_QUANTITIES_FILTERS = {
    "incoming_moves": lambda m: m._is_incoming()
    and (not m.origin_returned_move_id or m.to_refund),
    "outgoing_moves": lambda m: m._is_outgoing() and m.to_refund,
}


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_intercompany_kit_bom(self, product, company):
        """Return the phantom BOM of the kit moved by these moves.

        The moves are all the moves of an order line. The BOM is resolved
        from the product because with nested phantom BOMs the component moves
        point to a sub-BOM through their ``bom_line_id``, while the sync needs
        the top-level kit BOM. Raise when the moves do not match it anymore.
        """
        if not self.bom_line_id:
            return self.env["mrp.bom"]
        bom = self.env["mrp.bom"]._bom_find(
            product, company_id=company.id, bom_type="phantom"
        )[product]
        if not bom:
            self._raise_intercompany_kit_bom_changed(self.product_id)
        _, bom_lines = bom.explode(product, 1)
        self._check_intercompany_kit_bom_changed(
            {bom_line: bom_line_data["qty"] for bom_line, bom_line_data in bom_lines}
        )
        return bom

    def _get_intercompany_kit_qty_delivered(self, sale_line, sale_bom):
        done_moves = self.filtered(lambda m: m.state == "done" and not m.scrapped)
        if not sale_bom:
            return done_moves._get_intercompany_net_qty(DELIVERED_QUANTITIES_FILTERS)
        kit_qty_sold = sale_line.product_uom._compute_quantity(
            sale_line.product_uom_qty, sale_bom.product_uom_id
        )
        kit_qty_delivered = done_moves._compute_kit_quantities(
            sale_line.product_id, kit_qty_sold, sale_bom, DELIVERED_QUANTITIES_FILTERS
        )
        return sale_bom.product_uom_id._compute_quantity(
            kit_qty_delivered, sale_line.product_id.uom_id
        )

    def _get_intercompany_kit_qty_returned(self, sale_line, sale_bom):
        if not sale_bom:
            return sum(self.mapped("product_qty"))
        kit_qty_sold = sale_line.product_uom._compute_quantity(
            sale_line.product_uom_qty, sale_bom.product_uom_id
        )
        kit_qty_returned = self._compute_kit_quantities(
            sale_line.product_id, kit_qty_sold, sale_bom, KIT_QUANTITIES_FILTERS
        )
        return sale_bom.product_uom_id._compute_quantity(
            kit_qty_returned, sale_line.product_id.uom_id
        )

    def _get_intercompany_qty_received_by_bom_line(self):
        done_moves = self.filtered(lambda m: m.state == "done" and not m.scrapped)
        return {
            bom_line: moves._get_intercompany_net_qty(RECEIVED_QUANTITIES_FILTERS)
            for bom_line, moves in done_moves.grouped("bom_line_id").items()
        }

    def _get_intercompany_net_qty(self, filters):
        incoming_moves = self.filtered(filters["incoming_moves"])
        outgoing_moves = self.filtered(filters["outgoing_moves"])
        return (
            incoming_moves._get_intercompany_qty_in_product_uom()
            - outgoing_moves._get_intercompany_qty_in_product_uom()
        )

    def _get_intercompany_qty_in_product_uom(self):
        return sum(
            self.mapped(
                lambda m: m.product_uom._compute_quantity(
                    m.quantity, m.product_id.uom_id
                )
            )
        )

    def _set_intercompany_qty_done(self, qty):
        qty = max(qty, 0.0)
        for move in self:
            move_qty = qty if move == self[-1] else min(qty, move.product_qty)
            move._set_quantity_done(
                move.product_id.uom_id._compute_quantity(move_qty, move.product_uom)
            )
            qty -= move_qty
        self.picked = True

    def _check_intercompany_kit_tracking(self):
        """Reject tracked products: their lots cannot be synchronized.

        The moves are the products moved on either side of the kit, so this
        also covers the products of nested phantom BOMs. Their lots belong to
        the moved products, while the other company may move another product
        or decompose it with another BOM, so there is no reliable lot mapping.
        """
        tracked_products = self.product_id.filtered(
            lambda product: product.tracking != "none"
        )
        if tracked_products:
            raise UserError(
                self.env._(
                    "Inter-company kit synchronization does not support "
                    "tracked products: %(products)s",
                    products=", ".join(tracked_products.mapped("display_name")),
                )
            )

    def _check_intercompany_kit_bom_changed(self, qty_by_bom_line):
        """Check the moves still match the lines of the kit BOM.

        Each move must have a consumable BOM line of ``qty_by_bom_line``, and
        each consumable BOM line with a quantity must have a move, otherwise
        the BOM changed since the moves creation.
        """
        consu_lines = [
            line for line in qty_by_bom_line if line.product_id.type == "consu"
        ]
        bom_line_ids = {line.id for line in consu_lines}
        required_line_ids = {
            line.id
            for line in consu_lines
            if not float_is_zero(
                qty_by_bom_line[line], precision_rounding=line.product_uom_id.rounding
            )
        }
        stale_moves = self.filtered(lambda m: m.bom_line_id.id not in bom_line_ids)
        missing_lines = self.env["mrp.bom.line"].browse(
            required_line_ids - set(self.bom_line_id.ids)
        )
        if stale_moves or missing_lines:
            self._raise_intercompany_kit_bom_changed(
                stale_moves.product_id | missing_lines.product_id
            )

    def _raise_intercompany_kit_bom_changed(self, products):
        raise UserError(
            self.env._(
                "The kit BOM changed since the receipt creation: the quantities "
                "cannot be synchronized for %(products)s",
                products=", ".join(products.mapped("display_name")),
            )
        )
