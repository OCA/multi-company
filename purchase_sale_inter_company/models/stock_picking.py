# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    intercompany_picking_id = fields.Many2one(comodel_name='stock.picking')

    @api.multi
    def do_transfer(self):
        # Only DropShip pickings
        po_picks = self.browse()
        for pick in self.filtered(
                lambda x: x.location_dest_id.usage == 'customer').sudo():
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue
            purchase.picking_ids.write({'intercompany_picking_id': pick.id})
            for move_line in pick.move_line_ids:
                qty_done = move_line.qty_done
                po_move_lines = move_line.move_id.sale_line_id.\
                    auto_purchase_line_id.move_ids.mapped('move_line_ids')
                for po_move_line in po_move_lines:
                    if po_move_line.product_qty >= qty_done:
                        po_move_line.qty_done = qty_done
                        qty_done = 0.0
                    else:
                        po_move_line.qty_done = po_move_line.product_qty
                        qty_done -= po_move_line.product_qty
                    po_picks |= po_move_line.picking_id
                if qty_done and po_move_lines:
                    po_move_lines[-1:].qty_done += qty_done
                elif not po_move_lines:
                    raise UserError(_(
                        "There's no corresponding line in PO %s for assigning "
                        "qty from %s for product %s"
                    ) % (purchase.name, pick.name, move_line.product_id.name))
        # Transfer dropship pickings
        for po_pick in po_picks.sudo():
            po_pick.with_context(
                force_company=po_pick.company_id.id,
            ).action_done()
        return super(StockPicking, self).do_transfer()
