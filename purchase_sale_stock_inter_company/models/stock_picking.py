# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking", copy=False)

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
    
    def _get_product_intercompany_qty_done_dict(self, sale_move_lines, po_move_lines):
        product = po_move_lines[0].product_id
        qty_done = sum(sale_move_lines.mapped("qty_done"))
        res = {product: qty_done}
        return res

    def _set_intercompany_picking_qty_and_lot(self, purchase):
        self.ensure_one()
        po_picking_pending = purchase.picking_ids.filtered(
            lambda x: x.state not in ["done", "cancel"]
        )
        po_picking_pending.intercompany_picking_id = self.id
        if not self.intercompany_picking_id and po_picking_pending[0]:
            self.intercompany_picking_id = po_picking_pending[0]
        for move in self.move_ids:
            move_lines = move.move_line_ids.filtered(lambda x: x.quantity > 0)
            po_move_pending = move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                lambda x, ic_pick=self.intercompany_picking_id: x.picking_id == ic_pick
                and x.state not in ["done", "cancel"]
            )
            po_move_lines = po_move_pending.mapped("move_line_ids")
            move_line_diff = len(move_lines) - len(po_move_lines)
            # generate new move lines or remove if needed
            # example: In purchase order of C1, we have 2 move lines
            # and in reception of C2, we have 3 move lines(with lot or serial number)
            # then we need to create 1 more move line in purchase order of C1
            if move_line_diff > 0:
                new_move_line_vals = []
                for _index in range(move_line_diff):
                    vals = po_move_pending._prepare_move_line_vals()
                    new_move_line_vals.append(vals)
                po_move_lines |= po_move_lines.create(new_move_line_vals)
            elif move_line_diff < 0:
                # remove the extra move lines in the receipt of lot tracking product
                # example: In the receipt, we have 3 move lines for 3 different serials,
                # in the delivery we specify 2 serials. When validating the delivery and
                # creating back order, Odoo generates 3 move lines in the receipt, so
                # we need to remove 1 different move line in the receipt, otherwise it
                # will cause an error saying that we need to assign a lot or serial
                # for the remaining move line
                po_move_lines[len(move_lines) :].unlink()
                po_move_lines = po_move_lines[: len(move_lines)]
            # check and assign lots and quantity here
            for ml, po_ml in zip(move_lines, po_move_lines, strict=True):
                po_ml.quantity = ml.quantity
                if not ml.lot_id:
                    continue
                # search if the same lot exists in destination company
                dest_lot = ml._get_or_create_lot_intercompany(po_ml.company_id)
                po_ml.lot_id = dest_lot
        return po_picking_pending

    def _action_done(self):
        # Only DropShip pickings
        po_picks = self.browse()
        for pick in self.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        ).sudo():
            purchase = pick.sale_id.auto_purchase_order_id
            if not purchase:
                continue
            po_picking_pending = purchase.picking_ids.filtered(
                lambda x: x.state not in ["done", "cancel"]
            )
            po_picking_pending.intercompany_picking_id = pick.id
            if not pick.intercompany_picking_id and po_picking_pending[0]:
                pick.intercompany_picking_id = po_picking_pending[0]
            po_picks |= pick._set_intercompany_picking_qty_and_lot(purchase)
            pick._action_done_intercompany_actions(purchase)
        return super()._action_done()

    def _action_done_intercompany_actions(self, purchase):
        self.ensure_one()
        try:
            pick = self
            for move in pick.move_lines:
                move_lines = move.move_line_ids.filtered(lambda x: x.qty_done > 0)
                po_move_pending = (
                    move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                        lambda x, ic_pick=pick.intercompany_picking_id: x.picking_id
                        == ic_pick
                        and x.state not in ["done", "cancel"]
                    )
                )
                po_move_lines = po_move_pending.mapped("move_line_ids")
                move_line_diff = len(move_lines) - len(po_move_lines)
                # generate new move lines if needed
                # example: In purchase order of C1, we have 2 move lines
                # and in reception of C2, we have 3 move lines(with lot or serial number)
                # then we need to create 1 more move line in purchase order of C1
                if move_line_diff > 0:
                    new_move_line_vals = []
                    for _index in range(move_line_diff):
                        vals = po_move_pending._prepare_move_line_vals()
                        new_move_line_vals.append(vals)
                    po_move_lines |= po_move_lines.create(new_move_line_vals)
                # check and assign lots here
                # if len(move_lines) != (po_move_lines)
                # the zip will stop at the shortest list(only with qty_done > 0)
                # list(zip([1, 2], [1, 2, 3, 4])) = [(1, 1), (2, 2)]
                # list(zip([1, 2, 3, 4], [1, 2])) = [(1, 1), (2, 2)]
                for ml, po_ml in zip(move_lines, po_move_lines):
                    lot_id = ml.lot_id
                    if not lot_id:
                        continue
                    # search if the same lot exists in destination company
                    dest_lot = ml._get_or_create_lot_intercompany(po_ml.company_id)
                    po_ml.lot_id = dest_lot

        except Exception:
            if self.env.company.sync_picking_failure_action == "raise":
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
                and record.state == "done"
                and record.picking_type_code == "outgoing"
            ):
                if record.intercompany_picking_id:
                    try:
                        record._sync_receipt_with_delivery(
                            dest_company,
                            record.sale_id,
                        )
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
        purchase_order = sale_order.auto_purchase_order_id.sudo()
        if not (purchase_order and purchase_order.picking_ids):
            raise UserError(_("PO does not exist or has no receipts"))
        if self.intercompany_picking_id:
            dest_picking = self.intercompany_picking_id.with_user(intercompany_user.id)
            dest_move_qty_update_dict = {}
            for move in self.move_ids_without_package.sudo():
                # To identify the correct move to write to,
                # use both the SO-PO link and the intercompany_picking_id link
                dest_move = move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                    lambda x, pick=dest_picking: x.picking_id == pick
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
