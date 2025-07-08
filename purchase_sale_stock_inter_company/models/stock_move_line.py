from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        new_move_lines = super().create(vals_list)
        for move_line in new_move_lines.filtered(lambda x: x.state == "done"):
            po_moves = move_line._get_stock_moves_to_sync()
            for po_move in po_moves:
                po_move_line_vals = po_move._prepare_move_line_vals(
                    quantity=move_line.quantity
                )
                if move_line.lot_id:
                    dest_lot = move_line._get_or_create_lot_intercompany(
                        po_move.company_id
                    )
                    po_move_line_vals["lot_id"] = dest_lot.id
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
                    dest_lot = self._get_or_create_lot_intercompany(
                        po_move_line.company_id
                    )
                    field_value = dest_lot.id
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
        return {"quantity", "lot_id"}

    def _get_or_create_lot_intercompany(self, dest_company):
        # search if the same lot exists in destination company
        self.ensure_one()
        StockLot = self.env["stock.lot"].sudo()
        lot = self.lot_id.sudo()
        dest_lot = StockLot.search(
            [
                ("product_id", "=", lot.product_id.id),
                ("name", "=", lot.name),
                ("company_id", "=", dest_company.id),
            ],
            limit=1,
        )
        if not dest_lot:
            # if it doesn't exist, create it by copying from original company
            dest_lot = lot.copy({"company_id": dest_company.id, "name": lot.name})
        return dest_lot
