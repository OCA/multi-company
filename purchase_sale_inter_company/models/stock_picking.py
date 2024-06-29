# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking", copy=False)
    intercompany_return_picking_id = fields.Many2one(
        comodel_name="stock.picking", copy=False
    )

    @api.depends("intercompany_picking_id.state")
    def _compute_state(self):
        """
        If the picking is inter-company, it's an 'incoming'
        type of picking, and it has not been validated nor canceled
        we compute it's state based on the other picking state
        """
        res = super()._compute_state()
        for picking in self:
            if (
                picking.intercompany_picking_id
                and picking.picking_type_code == "incoming"
                and picking.state not in ["done", "cancel"]
            ):
                if picking.intercompany_picking_id.state in ["confirmed", "assigned"]:
                    picking.state = "waiting"
                else:
                    picking.state = picking.intercompany_picking_id.state

        return res

    def _warn_move_line_mismatch(self, ic_pick, product, ml, po_ml):
        self.ensure_one()
        note = _(
            "Mismatch between move lines (%s vs %s) with the "
            "corresponding PO picking %s for assigning "
            "quantities and lots from %s for product %s"
        ) % (len(ml), len(po_ml), ic_pick.name, self.name, product.name)
        _logger.warning(note)
        self.activity_schedule(
            "mail.mail_activity_data_warning",
            fields.Date.today(),
            note=note,
            # Try to notify someone relevant
            user_id=(
                self.sale_id.user_id.id
                or self.sale_id.team_id.user_id.id
                or SUPERUSER_ID,
            ),
        )

    def _sync_lots(self, ml, po_ml):
        lot_id = ml.lot_id
        if not lot_id:
            return
        # search if the same lot exists in destination company
        dest_lot_id = (
            self.env["stock.production.lot"]
            .sudo()
            .search(
                [
                    ("product_id", "=", lot_id.product_id.id),
                    ("name", "=", lot_id.name),
                    ("company_id", "=", po_ml.company_id.id),
                ],
                limit=1,
            )
        )
        if not dest_lot_id:
            # if it doesn't exist, create it by copying from original company
            dest_lot_id = lot_id.copy({"company_id": po_ml.company_id.id})
        po_ml.lot_id = dest_lot_id

    def _action_done(self):
        # sync lots for move lines on returns
        for pick in self.filtered(lambda x: x.intercompany_return_picking_id).sudo():
            ic_picking = pick.intercompany_return_picking_id
            dest_company = ic_picking.sudo().company_id
            if not dest_company.sync_picking:
                continue
            intercompany_user = dest_company.intercompany_sale_user_id
            for product in pick.move_lines.mapped("product_id"):
                if product.tracking == "none":
                    continue
                move_lines = (
                    pick.move_lines.filtered(
                        lambda x, prod=product: x.product_id == product
                    )
                    .mapped("move_line_ids")
                    .filtered("lot_id")
                )
                po_move_lines = (
                    ic_picking.with_user(intercompany_user)
                    .move_lines.filtered(lambda x, prod=product: x.product_id == prod)
                    .mapped("move_line_ids")
                )
                if len(move_lines) != len(po_move_lines):
                    pick._warn_move_line_mismatch(
                        ic_picking, product, move_lines, po_move_lines
                    )
                for ml, po_ml in zip(move_lines, po_move_lines):
                    pick._sync_lots(ml, po_ml)

        # sync lots for move lines on pickings
        for pick in self.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        ).sudo():
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue
            purchase.picking_ids.write({"intercompany_picking_id": pick.id})
            if not pick.intercompany_picking_id and purchase.picking_ids[0]:
                pick.write({"intercompany_picking_id": purchase.picking_ids[0]})
            pick._action_done_intercompany_actions(purchase)
        return super()._action_done()

    def _action_done_intercompany_actions(self, purchase):
        self.ensure_one()
        try:
            pick = self
            for move in pick.move_lines:
                move_lines = move.move_line_ids
                po_move_lines = move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                    lambda x, ic_pick=pick.intercompany_picking_id, prod=move.product_id: x.picking_id  # noqa
                    == ic_pick
                    and x.product_id == prod
                ).mapped(
                    "move_line_ids"
                )
                if len(move_lines) != len(po_move_lines):
                    pick._warn_move_line_mismatch(
                        pick.intercompany_picking_id,
                        move.product_id,
                        move_lines,
                        po_move_lines,
                    )
                for ml, po_ml in zip(move_lines, po_move_lines):
                    pick._sync_lots(ml, po_ml)

        except Exception:
            if self.env.company_id.sync_picking_failure_action == "raise":
                raise
            else:
                self._notify_picking_problem(purchase)

    def _notify_picking_problem(self, purchase):
        self.ensure_one()
        note = _(
            "Failure to confirm picking for PO %s. "
            "Original picking %s still confirmed, please check "
            "the other side manually."
        ) % (purchase.name, self.name)
        self.activity_schedule(
            "mail.mail_activity_data_warning",
            fields.Date.today(),
            note=note,
            # Try to notify someone relevant
            user_id=(
                self.company_id.notify_user_id.id
                or self.sale_id.user_id.id
                or self.sale_id.team_id.user_id.id
                or SUPERUSER_ID,
            ),
        )

    def button_validate(self):
        res = super().button_validate()
        for record in self.sudo():
            dest_company = (
                record.sale_id.partner_id.commercial_partner_id.ref_company_ids
            )
            if (
                dest_company
                and dest_company.sync_picking
                # only if it worked, not if wizard was raised
                and record.state == "done"
            ):
                try:
                    if (
                        record.picking_type_code == "outgoing"
                        and record.intercompany_picking_id
                    ):
                        record._sync_receipt_with_delivery(
                            dest_company,
                            record.sale_id,
                        )
                    elif (
                        record.picking_type_code == "incoming"
                        and record.intercompany_return_picking_id
                    ):
                        record._sync_receipt_with_delivery(dest_company, None)
                except Exception:
                    if record.company_id.sync_picking_failure_action == "raise":
                        raise
                    else:
                        record._notify_picking_problem(
                            record.sale_id.auto_purchase_order_id
                        )

        # if the flag is set, block the validation of the picking in the destination company
        if self.env.company.block_po_manual_picking_validation:
            for record in self:
                dest_company = record.partner_id.commercial_partner_id.ref_company_ids
                if (
                    dest_company and record.picking_type_code == "incoming"
                ) and record.state in ["done", "waiting", "assigned"]:
                    raise UserError(
                        _(
                            "Manual validation of the picking is not allowed"
                            " in the destination company."
                        )
                    )
        return res

    def _sync_receipt_with_delivery(self, dest_company, sale_order):
        self.ensure_one()
        intercompany_user = dest_company.intercompany_sale_user_id

        # sync SO return to PO return
        if self.intercompany_return_picking_id:
            moves = [(m, m.quantity_done) for m in self.move_ids_without_package]
            dest_picking = self.intercompany_return_picking_id.with_user(
                intercompany_user
            )
            all_dest_moves = self.intercompany_return_picking_id.with_user(
                intercompany_user
            ).move_lines
            for move, qty in moves:
                dest_moves = all_dest_moves.filtered(
                    lambda x, prod=move.product_id: x.product_id == prod
                )
                remaining_qty = qty
                remaining_ml = move.move_line_ids
                while dest_moves and remaining_qty > 0.0:
                    dest_move = dest_moves[0]
                    to_assign = min(
                        remaining_qty,
                        dest_move.product_uom_qty - dest_move.quantity_done,
                    )
                    final_qty = dest_move.quantity_done + to_assign
                    for line, dest_line in zip(remaining_ml, dest_move.move_line_ids):
                        # Assuming the order of move lines is the same on both moves
                        # is risky but what would be a better option?
                        dest_line.sudo().write(
                            {
                                "qty_done": line.qty_done,
                            }
                        )
                    dest_move.quantity_done = final_qty
                    remaining_qty -= to_assign
                    if dest_move.quantity_done == dest_move.product_qty:
                        dest_moves -= dest_move
            dest_picking._action_done()

        # sync SO to PO picking
        if self.intercompany_picking_id:
            purchase_order = sale_order.auto_purchase_order_id.sudo()
            if not (purchase_order and purchase_order.picking_ids):
                raise UserError(_("PO does not exist or has no receipts"))
            dest_picking = self.intercompany_picking_id.with_user(intercompany_user.id)
            dest_move_qty_update_dict = {}
            for move in self.move_ids_without_package.sudo():
                # To identify the correct move to write to,
                # use both the SO-PO link and the intercompany_picking_id link
                # as well as the product, to support the "kit" case where an order line
                # unpacks into several move lines
                dest_move = move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                    lambda x, pick=dest_picking, prod=move.product_id: x.picking_id
                    == pick
                    and x.product_id == prod
                )
                for line, dest_line in zip(move.move_line_ids, dest_move.move_line_ids):
                    # Assuming the order of move lines is the same on both moves
                    # is risky but what would be a better option?
                    dest_line.sudo().write(
                        {
                            "qty_done": line.qty_done,
                        }
                    )
                dest_move_qty_update_dict.setdefault(dest_move, 0.0)
                dest_move_qty_update_dict[dest_move] += move.quantity_done
            # "No backorder" case splits SO moves in two while PO stays the same.
            # Aggregating writes per each PO move makes sure qty does not get overwritten
            for dest_move, qty_done in dest_move_qty_update_dict.items():
                dest_move.quantity_done = qty_done
            dest_picking.sudo().with_context(
                cancel_backorder=bool(
                    self.env.context.get("picking_ids_not_to_backorder")
                )
            )._action_done()

    def _update_extra_data_in_picking(self, picking):
        if hasattr(self, "_cal_weight"):  # from delivery module
            self._cal_weight()
