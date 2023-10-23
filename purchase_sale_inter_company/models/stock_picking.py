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
        for pick in self.filtered(
                lambda x: x.location_dest_id.usage == 'customer').sudo():
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue
            purchase.picking_ids.write({'intercompany_picking_id': pick.id})
            if not pick.intercompany_picking_id and purchase.picking_ids[0]:
                pick.write({"intercompany_picking_id": purchase.picking_ids[0].id})
            for move_line in pick.move_line_ids:
                po_move_lines = move_line.move_id.sale_line_id. \
                    auto_purchase_line_id.move_ids.filtered(
                        lambda m: m.picking_id == pick.intercompany_picking_id
                    ).mapped('move_line_ids')
                if not po_move_lines:
                    raise UserError(_(
                        "There's no corresponding line in PO %s for assigning "
                        "qty from %s for product %s"
                    ) % (purchase.name, pick.name, move_line.product_id.name))
        return super().action_done()

    def button_validate(self):
        res = super().button_validate()
        for record in self.sudo():
            dest_company = record.partner_id.commercial_partner_id.ref_company_ids
            if (
                dest_company
                and dest_company.sync_picking
                and record.state == "done"
                and record.picking_type_code == "outgoing"
            ):
                if record.intercompany_picking_id:
                    record._sync_receipt_with_delivery(
                        dest_company,
                        record.sale_id,
                    )
        return res

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
            for picking_move in self.move_ids_without_package.sudo():
                # To identify the correct move to write to,
                # use both the SO-PO link and the intercompany_picking_id link
                dest_picking_move = picking_move.sale_line_id.\
                    auto_purchase_line_id.move_ids.filtered(
                        lambda m: m.picking_id == dest_picking)
                for picking_line, dest_picking_line in zip(
                        picking_move.move_line_ids, dest_picking_move.move_line_ids):
                    # Assuming the order of move lines is the same on both moves
                    # is risky but what would be a better option?
                    dest_picking_line.sudo().write({
                        'qty_done': picking_line.qty_done,
                    })
                dest_picking_move.sudo().write({
                    'quantity_done': picking_move.quantity_done,
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
