from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        new_move_lines = super().create(vals_list)
        # When a picking is unlocked, the user can add new moves.
        # So, create the corresponding move lines in the intercompany picking.
        for move_line in new_move_lines.filtered(lambda x: x.state == "done"):
            po_moves = move_line._get_stock_moves_to_sync()
            for po_move in po_moves:
                po_move_line_vals = po_move._prepare_move_line_vals(
                    quantity=move_line.quantity
                )
                if move_line.lot_id:
                    po_move_line_vals["lot_id"] = (
                        move_line._ensure_lot_multicompany().id
                    )
                po_move_line_vals["quantity"] = move_line.quantity
                self.sudo().create(po_move_line_vals)
        return new_move_lines

    def write(self, vals):
        moves_to_sync = {}
        fields_to_sync = self._get_fields_to_sync_intercompany()
        if fields_to_sync.intersection(set(vals.keys())):
            for move_line in self:
                purchase_line_origin = (
                    move_line.move_id.sale_line_id.sudo().auto_purchase_line_id
                )
                if move_line.state == "done" and purchase_line_origin:
                    moves_to_sync.setdefault(move_line, move_line.lot_id.name or "")
        res = super().write(vals)
        for move_line, lot_name in moves_to_sync.items():
            move_line._sync_intercompany_move(lot_name, vals)
        return res

    def _sync_intercompany_move(self, lot_name, vals):
        """
        Sync the intercompany stock move lines
        with the changes made in this move line.
        :param lot_name: the name of the lot to match the move lines
        :param vals: the values to sync
        """
        self.ensure_one()
        fields_to_sync = self._get_fields_to_sync_intercompany()
        po_moves = self._get_stock_moves_to_sync()
        for po_move in po_moves:
            po_move_line = po_move.move_line_ids.filtered(
                lambda x: not self.lot_id or x.lot_id.name == lot_name
            )
            if not po_move_line:
                continue
            vals_to_write = {}
            for field in fields_to_sync:
                if field not in vals:
                    continue
                field_value = self[field]
                if field == "lot_id" and field_value:
                    field_value = self._ensure_lot_multicompany().id
                vals_to_write[field] = field_value
            if vals_to_write:
                po_move_line.write(vals_to_write)

    def _get_stock_moves_to_sync(self):
        """
        Get the stock moves that need to be synced with the intercompany move.
        """
        self.ensure_one()
        purchase_line_origin = self.move_id.sale_line_id.sudo().auto_purchase_line_id
        po_moves = self.env["stock.move"]
        if purchase_line_origin:
            po_moves = purchase_line_origin.move_ids.filtered(
                lambda m: m.picking_id
                == self.move_id.picking_id.intercompany_picking_id
                and m.product_id == self.product_id
            )
        return po_moves

    @api.model
    def _get_fields_to_sync_intercompany(self):
        """
        Get the fields that need to be synced with the intercompany move line.
        :return: set of field names
        """
        return {"quantity", "lot_id"}

    def _ensure_lot_multicompany(self):
        """
        Ensure that the lot can be shared across multiple companies.
        """
        self.ensure_one()
        lot = self.lot_id.sudo()
        if lot.company_id:
            lot.company_id = False
        return lot
