from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_or_create_lot_intercompany(self, dest_company):
        # search if the same lot exists in destination company
        self.ensure_one()
        ProductionLot = self.env["stock.lot"].sudo()
        lot = self.lot_id
        dest_lot = ProductionLot.search(
            [
                ("product_id", "=", lot.product_id.id),
                ("name", "=", lot.name),
                ("company_id", "=", dest_company.id),
            ],
            limit=1,
        )
        if not dest_lot:
            # if it doesn't exist, create it by copying from original company
            dest_lot = lot.sudo().copy(
                {"company_id": dest_company.id, "name": lot.name}
            )
        return dest_lot
