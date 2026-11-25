# Copyright 2026 Tecnativa - Carlos Lopez

from odoo import Command, models


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_return(self):
        new_picking = super()._create_return()
        if self._should_create_intercompany_return():
            return_wizard = self._create_intercompany_return_wizard(new_picking)
            # Nothing left to return in the purchase company: the sync of the
            # return will flag the mismatch
            if any(
                not line.uom_id.is_zero(line.quantity)
                for line in return_wizard.product_return_moves
            ):
                return_wizard.with_context(skip_create_returns=True)._create_return()
        return new_picking

    def _should_create_intercompany_return(self):
        if (
            self.env.context.get("skip_create_returns")
            or not self.picking_id._is_intercompany_delivery()
        ):
            return False
        # The return is created as superuser: only trust a picking of the
        # purchase order linked to the sale order
        purchase = self.picking_id.sale_id.sudo().auto_purchase_order_id
        intercompany_picking = self.picking_id.sudo().intercompany_picking_id
        return bool(purchase) and intercompany_picking.purchase_id == purchase

    def _create_intercompany_return_wizard(self, new_picking):
        intercompany_picking = self.picking_id.intercompany_picking_id
        dest_company = intercompany_picking.sudo().company_id
        vals = {"picking_id": intercompany_picking.id}
        # Superuser restricted to the purchase company: the user returning
        # the delivery may have no access to it
        return_wizard = (
            self.env["stock.return.picking"]
            .sudo()
            .with_context(
                active_id=intercompany_picking.id,
                allowed_company_ids=dest_company.ids,
            )
            .create(vals)
        )
        # stock_picking_return_lot compatibility
        if "lot_id" in return_wizard.product_return_moves._fields:
            # Match on product and lot: untracked products have no lot
            returned = {
                (line.product_id, line.lot_id) for line in self.product_return_moves
            }
            exclude_moves = return_wizard.product_return_moves.filtered(
                lambda line: (line.product_id, line.lot_id) not in returned
            )
        else:
            exclude_moves = return_wizard.product_return_moves.filtered(
                lambda line: line.product_id not in self.product_return_moves.product_id
            )
        return_wizard.product_return_moves = [
            Command.unlink(prm.id) for prm in exclude_moves
        ]
        for wizard_line in self.product_return_moves:
            dest_line = return_wizard.product_return_moves.filtered(
                lambda line, wizard_line=wizard_line: (
                    line.product_id == wizard_line.product_id
                )
            )
            # stock_picking_return_lot compatibility
            if "lot_id" in wizard_line._fields:
                dest_line = dest_line.filtered(
                    lambda x, wizard_line=wizard_line: x.lot_id == wizard_line.lot_id
                )
            product = wizard_line.product_id
            qty = wizard_line.uom_id._compute_quantity(
                wizard_line.quantity, product.uom_id
            )
            for line in dest_line:
                # Never return more than received minus what is already returned
                move = line.move_id
                returned_moves = move.returned_move_ids.filtered(
                    lambda m: m.state != "cancel"
                )
                returnable_qty = move.product_uom._compute_quantity(
                    move.quantity, product.uom_id
                ) - sum(
                    m.product_uom._compute_quantity(m.product_uom_qty, product.uom_id)
                    for m in returned_moves
                )
                line_qty = max(min(qty, returnable_qty), 0.0)
                qty -= line_qty
                line.quantity = product.uom_id._compute_quantity(line_qty, line.uom_id)
        return return_wizard
