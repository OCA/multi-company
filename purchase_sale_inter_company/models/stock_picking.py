# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    intercompany_picking_id = fields.Many2one(comodel_name='stock.picking', copy=False)

    @api.multi
    def action_done(self):
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
        return super(StockPicking, self).action_done()

    def button_validate(self):
        is_intercompany = self.env["res.company"].search(
            [("partner_id", "=", self.partner_id.id)]
        ) or self.env["res.company"].search(
            [("partner_id", "=", self.partner_id.parent_id.id)]
        )
        if is_intercompany and self.company_id.sync_picking \
                and self.picking_type_code == "outgoing":
            sale_order = self.sale_id
            dest_company = sale_order.partner_id.ref_company_ids
            for rec in self:
                if rec.intercompany_picking_id:
                    rec._sync_receipt_with_delivery(
                        dest_company,
                        sale_order,
                    )
        return super().button_validate()

    def _sync_receipt_with_delivery(self, dest_company, sale_order):
        self.ensure_one()
        intercompany_user = dest_company.intercompany_user_id
        purchase_order = sale_order.auto_purchase_order_id.sudo()
        if (
            not purchase_order
            or not purchase_order.sudo(intercompany_user.id).picking_ids
        ):
            raise UserError(_("PO does not exist or has no receipts"))
        if self.intercompany_picking_id:
            dest_picking = self.intercompany_picking_id.sudo(intercompany_user.id)
            for picking_move in self.move_ids_without_package:
                dest_picking_move = dest_picking.sudo(
                ).move_ids_without_package.filtered(
                    lambda l: l.product_id.id == picking_move.product_id.id)
                dest_picking_move.sudo().write({
                    'quantity_done': picking_move.quantity_done,
                })
            for picking_line in self.move_line_ids_without_package:
                dest_picking_line = dest_picking.sudo(
                ).move_line_ids_without_package.filtered(
                    lambda l: l.product_id.id == picking_line.product_id.id)
                dest_picking_line.sudo().write({
                    'qty_done': picking_line.qty_done,
                })

    def action_generate_backorder_wizard(self):
        view = self.env.ref('stock.view_backorder_confirmation')
        wiz = self.env['stock.backorder.confirmation'].with_context(
            picking_id=self.id
        ).create({'pick_ids': [(4, p.id) for p in self]})
        return {
            'name': _('Create Backorder?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.backorder.confirmation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }

    def _update_extra_data_in_picking(self, picking):
        if hasattr(self, "_cal_weight"):  # from delivery module
            self._cal_weight()
