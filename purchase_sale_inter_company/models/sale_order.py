# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    auto_purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Source Purchase Order",
        readonly=True,
        copy=False,
    )

    def action_confirm(self):
        for order in self.filtered("auto_purchase_order_id"):
            for line in order.order_line.sudo():
                if line.auto_purchase_line_id:
                    line.auto_purchase_line_id.price_unit = line.price_unit
        res = super().action_confirm()
        for sale_order in self.sudo():
            dest_company = sale_order.partner_id.ref_company_ids
            if (
                sale_order.auto_purchase_order_id
                and dest_company
                and dest_company.sync_picking
            ):
                pickings = sale_order.picking_ids
                po_company = sale_order.sudo().auto_purchase_order_id.company_id
                purchase_picking = sale_order.auto_purchase_order_id.with_user(
                    po_company.intercompany_sale_user_id.id
                ).picking_ids

                if len(pickings) == len(purchase_picking) == 1:
                    # thus they have the same moves and move lines with same quantities
                    purchase_picking.write({"intercompany_picking_id": pickings.id})
                    pickings.write({"intercompany_picking_id": purchase_picking.id})
                if len(pickings) > 1 and len(purchase_picking) == 1:
                    # If there are several pickings in the sale order and one
                    # in the purchase order, then split the receipt
                    # thus we need to recreate new moves and moves lines, as they differ
                    purchase_moves = purchase_picking.move_ids_without_package
                    purchase_move_lines = purchase_picking.move_line_ids_without_package
                    new_pickings = self.env["stock.picking"].with_user(
                        po_company.intercompany_sale_user_id.id
                    )
                    for i, pick in enumerate(pickings):
                        moves = pick.move_ids_without_package
                        new_moves = self.env["stock.move"].with_user(
                            po_company.intercompany_sale_user_id.id
                        )
                        new_move_lines = self.env["stock.move.line"].with_user(
                            po_company.intercompany_sale_user_id.id
                        )
                        for move in moves:
                            purchase_move = purchase_moves.filtered(
                                lambda m: m.product_id.id == move.product_id.id
                            )[:1]
                            new_move = purchase_move.with_user(
                                po_company.intercompany_sale_user_id.id
                            ).copy(
                                {
                                    "picking_id": purchase_picking.id
                                    if i == 0
                                    else False,
                                    "name": move.name,
                                    "product_uom_qty": move.product_uom_qty,
                                    "product_uom": move.product_uom.id,
                                    "price_unit": -move.price_unit,
                                    "note": move.note,
                                    "create_date": move.create_date,
                                    "date": move.date,
                                    "date_deadline": move.date_deadline,
                                    "state": move.state,
                                }
                            )
                            new_move._update_extra_data_in_move(move)
                            new_moves |= new_move
                            for move_line in move.move_line_ids.filtered(
                                lambda l: l.package_level_id
                                and not l.picking_type_entire_packs
                            ):
                                purchase_move_line = purchase_move_lines.filtered(
                                    lambda l: l.product_id.id == move_line.product_id.id
                                )[:1]
                                new_move_line = purchase_move_line.with_user(
                                    po_company.intercompany_sale_user_id.id
                                ).copy(
                                    {
                                        "picking_id": purchase_picking.id
                                        if i == 0
                                        else False,
                                        "move_id": new_move.id,
                                        "product_uom_qty": move_line.product_uom_qty,
                                        "product_uom_id": move_line.product_uom_id.id,
                                        "create_date": move_line.create_date,
                                        "date": move_line.date,
                                        "state": move_line.state,
                                    }
                                )
                                new_move_line._update_extra_data_in_move_line(move_line)
                                new_move_lines |= new_move_line
                        if i == 0:
                            purchase_picking.with_user(
                                purchase_picking.company_id.intercompany_sale_user_id.id
                            ).write(
                                {
                                    "intercompany_picking_id": pick.id,
                                    "note": pick.note,
                                    "create_date": pick.create_date,
                                    "state": pick.state,
                                }
                            )
                            new_pick = purchase_picking
                        else:
                            new_pick = purchase_picking.with_user(
                                po_company.intercompany_sale_user_id.id
                            ).copy(
                                {
                                    "move_ids_without_package": [
                                        (6, False, new_moves.ids)
                                    ],
                                    "move_line_ids_without_package": [
                                        (6, False, new_move_lines.ids)
                                    ],
                                    "intercompany_picking_id": pick.id,
                                    "note": pick.note,
                                    "create_date": pick.create_date,
                                    "state": pick.state,
                                }
                            )
                            new_pick._update_extra_data_in_picking(pick)
                        pick.write({"intercompany_picking_id": new_pick.id})
                        new_pickings |= new_pick
                    purchase_move_lines.unlink()
                    purchase_moves._action_cancel()
                    purchase_moves.unlink()
                    purchase_picking._update_extra_data_in_picking(pickings[:1])
                    new_pickings.sudo().action_assign()

        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Source Purchase Order Line",
        readonly=True,
        copy=False,
    )
