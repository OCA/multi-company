# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    intercompany_picking_id = fields.Many2one(comodel_name="stock.picking", copy=False)
    # to silence the warning
    # Field stock.picking.state should be declared with recursive=True
    state = fields.Selection(recursive=True)

    @api.depends("intercompany_picking_id.move_ids.state")
    def _compute_state(self):
        res = super()._compute_state()
        # If the picking is inter-company, it's an 'incoming'
        # type of picking, and it has not been validated nor canceled
        # we compute it's state based on the other picking state
        for picking in self.filtered(
            lambda pick: (
                pick._is_intercompany_reception()
                and pick.state not in ["done", "cancel"]
            )
        ):
            # intercompany_picking_id is set when the picking is validated
            # meanwhile, the state should remain in 'waiting'
            if not picking.intercompany_picking_id:
                picking.state = "waiting"
            elif picking.intercompany_picking_id.state not in ["done", "cancel"]:
                if picking.intercompany_picking_id.state in ["confirmed", "assigned"]:
                    picking.state = "waiting"
                else:
                    picking.state = picking.intercompany_picking_id.state

        return res

    def button_validate(self):
        # if the flag is set,
        # block the validation of the picking in the destination company
        if self.filtered(
            lambda picking: (
                picking.company_id.block_po_manual_picking_validation
                and (
                    picking._is_intercompany_reception()
                    or picking._is_intercompany_return_delivery()
                )
                and picking.state in ["done", "waiting", "assigned"]
            )
        ):
            raise UserError(
                self.env._(
                    "Manual validation of the picking is not allowed"
                    " in the destination company."
                )
            )
        return super().button_validate()

    def _action_done(self):
        res = super()._action_done()
        # Only DropShip pickings
        for picking in self.filtered(
            lambda pick: (
                pick._is_intercompany_delivery()
                or pick._is_intercompany_return_reception()
            )
        ):
            purchase = picking.sale_id.sudo().auto_purchase_order_id
            if picking._is_intercompany_return_reception():
                # Only set by this sync: ignore any value written before
                picking.sudo().intercompany_picking_id = False
                picking.sudo()._create_intercompany_return()
            picking.sudo()._action_done_intercompany_actions(purchase)
        return res

    def _create_intercompany_return(self):
        """
        Create the return of the inter-company receipt in the purchase company
        for the quantities returned with this picking.
        :return: browse_record(stock.picking) the purchase return
        """
        self.ensure_one()
        purchase = self.sale_id.sudo().auto_purchase_order_id
        po_picking = self.return_id.intercompany_picking_id.sudo()
        # The return is created as superuser: only trust a picking of the
        # purchase order linked to the sale order
        if not purchase or po_picking.purchase_id != purchase:
            return self.browse()
        # Superuser restricted to the purchase company: the user validating
        # the return may have no access to it
        po_return = po_picking.with_context(
            allowed_company_ids=po_picking.company_id.ids
        )._create_return()
        returned_qty = defaultdict(float)
        for move in self.move_ids.filtered(lambda m: m.state == "done"):
            returned_qty[move.product_id] += move.uom_id._compute_quantity(
                move.quantity, move.product_id.uom_id
            )
        for po_move in po_return.move_ids:
            product = po_move.product_id
            origin_move = po_move.origin_returned_move_id
            # Never return more than received minus what is already returned
            returned_moves = origin_move.returned_move_ids.filtered(
                lambda m: m.state != "cancel" and m not in po_return.move_ids
            )
            returnable_qty = origin_move.uom_id._compute_quantity(
                origin_move.quantity, product.uom_id
            ) - sum(
                m.uom_id._compute_quantity(m.product_uom_qty, product.uom_id)
                for m in returned_moves
            )
            qty = max(min(returned_qty[product], returnable_qty), 0.0)
            returned_qty[product] -= qty
            po_move.product_uom_qty = product.uom_id._compute_quantity(
                qty, po_move.uom_id
            )
        po_return.move_ids.filtered(
            lambda m: m.uom_id.is_zero(m.product_uom_qty)
        ).unlink()
        if not po_return.move_ids:
            po_return.unlink()
            return self.browse()
        po_return.action_confirm()
        self.intercompany_picking_id = po_return
        return po_return

    def _get_product_intercompany_qty_done_dict(self, sale_move_lines, po_move_lines):
        """
        Get the total quantity done
        for the given sale move lines and purchase move lines.
        This is used to update the purchase order with the quantities
        received in the inter-company picking.
        :param sale_move_lines:
            browse_record(stock.move.line) Sale move lines to consider
        :param po_move_lines:
            browse_record(stock.move.line) Purchase move lines to consider
        :return: dict with product as key and total quantity done as value
        """
        product = po_move_lines.product_id
        quantity = sum(sale_move_lines.mapped("quantity"))
        res = {product: quantity}
        return res

    def _action_done_intercompany_actions(self, purchase):
        self.ensure_one()
        try:
            dest_company = purchase.company_id
            intercompany_user = dest_company.intercompany_sale_user_id
            po_picking_pending = purchase.picking_ids.filtered(
                lambda x: x.state not in ["done", "cancel"]
            )
            if not purchase.picking_ids:
                raise UserError(
                    self.env._(
                        "There's no corresponding line in PO %(po)s"
                        " for picking %(pick)s.",
                        po=purchase.name,
                        pick=self.name,
                    )
                )
            po_picking_pending.intercompany_picking_id = self.id
            # The picking is synced as superuser: only a picking of the
            # purchase order linked to the sale order can be used
            if self.intercompany_picking_id.sudo().purchase_id != purchase:
                self.intercompany_picking_id = False
            if not self.intercompany_picking_id and po_picking_pending:
                self.intercompany_picking_id = po_picking_pending[0]
            # Only the purchase company: the inter-company user may not
            # have access to the company validating the delivery
            dest_picking = self.intercompany_picking_id.with_user(
                intercompany_user
            ).with_context(allowed_company_ids=dest_company.ids)
            for move in self.move_ids.filtered(lambda m: m.state != "cancel"):
                move_lines = move.move_line_ids.filtered(lambda x: x.quantity > 0)
                # To identify the correct move to write to,
                # use both the SO-PO link and the intercompany_picking_id link
                po_move_pending = (
                    move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                        lambda x, ic_pick=dest_picking: (
                            x.picking_id == ic_pick
                            and x.state not in ["done", "cancel"]
                        )
                    )
                )
                # stock_restrict_lot and purchase_sale_lot_intercompany compatibility
                if "restrict_lot_id" in move._fields and move.restrict_lot_id:
                    po_move_pending = po_move_pending.filtered(
                        lambda x, move=move: x.restrict_lot_id == move.restrict_lot_id
                    )
                po_move_lines = po_move_pending.move_line_ids
                # Check if there are any done moves that can be used for returns
                po_moves_done = (
                    move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                        lambda sm: sm.state == "done" and not sm._is_purchase_return()
                    )
                )
                # If all the PO moves are done (e.g. delivery after a return),
                # create new moves from them. A pending PO move (backorder or
                # inter-company return) must be used as is.
                if (
                    not po_move_pending
                    and po_moves_done
                    and not self._is_intercompany_return_reception()
                ):
                    # Calculate the quantity from the move_lines
                    qty = sum(move_lines.mapped("quantity"))
                    po_move_pending = po_moves_done[-1].copy(
                        {
                            "product_uom_qty": qty,
                            "quantity": qty,
                            "move_line_ids": False,
                        }
                    )
                else:
                    # Don't raise an error
                    # if there are no move_line_ids and the location is transit.
                    # In vendor locations, reservations are bypassed,
                    # but in transit locations,
                    # we need to create the move lines to assign lots/serials.
                    if not po_move_pending or (
                        not po_move_lines
                        and move.location_dest_id.usage != "transit"
                        and not move.picking_id._is_intercompany_return_reception()
                    ):
                        note = self.env._(
                            "Mismatch between move lines with the "
                            "corresponding PO %(po)s for assigning "
                            "quantities and lots from %(pick_name)s for "
                            "product %(product)s",
                            po=purchase.name,
                            pick_name=self.name,
                            product=move.product_id.display_name,
                        )
                        purchase.activity_schedule(
                            "mail.mail_activity_data_warning",
                            date_deadline=fields.Date.today(),
                            note=note,
                            user_id=(
                                self.sale_id.user_id.id
                                or self.sale_id.team_id.user_id.id
                                or SUPERUSER_ID
                            ),
                        )
                        continue
                po_move_lines = po_move_pending.move_line_ids
                move_line_diff = len(move_lines) - len(po_move_lines)
                # generate new move lines if needed
                # example: In purchase order of C1, we have 2 move lines
                # and in reception of C2,
                # we have 3 move lines(with lot or serial number)
                # then we need to create 1 more move line in purchase order of C1
                if move_line_diff > 0:
                    new_move_line_vals = []
                    for _index in range(move_line_diff):
                        vals = po_move_pending[:1]._prepare_move_line_vals()
                        new_move_line_vals.append(vals)
                    po_move_lines |= po_move_lines.create(new_move_line_vals)
                elif move_line_diff < 0:
                    # remove the extra move lines in the receipt of lot tracking product
                    # example:
                    # In the receipt, we have 3 move lines for 3 different serials,
                    # in the delivery we specify 2 serials.
                    # When validating the delivery and creating back order,
                    # Odoo generates 3 move lines in the receipt,
                    # so we need to remove 1 different move line in the receipt,
                    # otherwise it will cause an error
                    # saying that we need to assign a lot or serial
                    # for the remaining move line
                    extra_lines = po_move_lines[len(move_lines) :]
                    done_extra = extra_lines.filtered(
                        lambda ml: ml.picking_id.state == "done"
                    )
                    done_extra.write({"quantity": 0})
                    (extra_lines - done_extra).unlink()
                    po_move_lines = po_move_lines[: len(move_lines)]
                # check and assign lots here
                # if len(move_lines) != (po_move_lines)
                # the zip will stop at the shortest list(only with quantity > 0)
                # list(zip([1, 2], [1, 2, 3, 4])) = [(1, 1), (2, 2)]
                # list(zip([1, 2, 3, 4], [1, 2])) = [(1, 1), (2, 2)]
                for ml, po_ml in zip(move_lines, po_move_lines, strict=True):
                    # Assuming the order of move lines is the same on both moves
                    # is risky but what would be a better option?
                    product_qty_done = self._get_product_intercompany_qty_done_dict(
                        ml, po_ml
                    )
                    po_ml.write(
                        {
                            "quantity": product_qty_done.get(po_ml.product_id) or 0,
                            "picked": True,
                        }
                    )
                    lot_id = ml.lot_id
                    if not lot_id:
                        continue
                    po_ml.lot_id = ml._ensure_lot_multicompany()
            # Refresh po_move_pending to filter out any unlinked/deleted moves
            po_move_pending = po_move_pending.filtered(lambda x: x.exists())
            if po_move_pending and dest_company.sync_picking and self.state == "done":
                dest_picking.sudo().with_context(
                    cancel_backorder=bool(
                        self.env.context.get("picking_ids_not_to_backorder")
                    )
                )._action_done()
        except Exception:
            if purchase.company_id.sync_picking_failure_action == "raise":
                raise
            else:
                self._notify_picking_problem(purchase)

    def _notify_picking_problem(self, purchase):
        """
        Create an activity to notify of a problem when syncing the intercompany picking.
        :param purchase: browse_record(purchase.order)
        """
        self.ensure_one()
        note = self.env._(
            "Failure to confirm picking for PO %(purchase_name)s. "
            "Original picking %(picking_name)s still confirmed, please check "
            "the other side manually.",
            purchase_name=purchase.name,
            picking_name=self.name,
        )
        self.activity_schedule(
            "mail.mail_activity_data_warning",
            fields.Date.context_today(self),
            note=note,
            # Try to notify someone relevant
            user_id=(
                self.company_id.notify_user_id.id
                or self.sale_id.user_id.id
                or self.sale_id.team_id.user_id.id
                or SUPERUSER_ID
            ),
        )

    def _is_intercompany_reception(self):
        """
        Check if the picking is an inter-company reception.
        :return: bool
        """
        return (
            not self.return_id
            and self.location_id.usage in ["supplier", "transit"]
            and self.purchase_id.sudo().intercompany_sale_order_id
        )

    def _is_intercompany_delivery(self):
        """
        Check if the picking is an inter-company delivery.
        :return: bool
        """
        return (
            # An exchange is the return of an inter-company return
            (not self.return_id or self.return_id._is_intercompany_return_reception())
            and self.location_dest_id.usage in ["customer", "transit"]
            and self.sale_id.sudo().auto_purchase_order_id
        )

    def _is_intercompany_return_reception(self):
        """
        Check if the picking is an inter-company return reception.
        :return: bool
        """
        return (
            self.return_id
            and self.location_id.usage in ["customer", "transit"]
            and self.return_id._is_intercompany_delivery()
        )

    def _is_intercompany_return_delivery(self):
        """
        Check if the picking is an inter-company return delivery.
        :return: bool
        """
        return (
            self.return_id
            and self.location_dest_id.usage in ["supplier", "transit"]
            and self.return_id._is_intercompany_reception()
        )
