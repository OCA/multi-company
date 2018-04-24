# Copyright 2018 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import Warning as UserError


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
            for move_line in pick.move_line_ids:
                qty_done = move_line.qty_done
                # po_move_lines = purchase.sudo().picking_ids.mapped(
                #     'move_line_ids').filtered(
                #         lambda x: x.product_id == move_line.product_id and
                #         not x.processed_boolean)
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
                    raise UserError(
                        _('Any picking to assign units from %s (%s)') %
                        (pick.name, purchase.name))
                    # TODO: Create new DropShip Picking
            pick.intercompany_picking_id = po_move_line.picking_id
            po_move_line.picking_id.intercompany_picking_id = pick
        # Done dropship pickings
        if po_picks:
            po_self = self.sudo().with_context(
                force_company=po_picks[0].company_id.id)
            for po_pick in po_picks:
                po_self.env['stock.backorder.confirmation'].create(
                    {'pick_id': po_pick.id}).process()
        return super(StockPicking, self).do_transfer()
