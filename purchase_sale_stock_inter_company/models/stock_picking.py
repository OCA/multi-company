# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
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
            lambda pick: pick._is_intercompany_reception()
            and pick.state not in ["done", "cancel"]
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
            lambda picking: picking.company_id.block_po_manual_picking_validation
            and picking._is_intercompany_reception()
            and picking.state in ["done", "waiting", "assigned"]
        ):
            raise UserError(
                _(
                    "Manual validation of the picking is not allowed"
                    " in the destination company."
                )
            )
        return super().button_validate()

    def _action_done(self):
        res = super()._action_done()
        # Only DropShip pickings
        for picking in self.filtered(lambda pick: pick._is_intercompany_delivery()):
            purchase = picking.sale_id.sudo().auto_purchase_order_id
            picking.sudo()._action_done_intercompany_actions(purchase)
        return res

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
            po_picking_pending.intercompany_picking_id = self.id
            if not self.intercompany_picking_id and po_picking_pending:
                self.intercompany_picking_id = po_picking_pending[0]
            dest_picking = self.intercompany_picking_id.with_user(
                intercompany_user
            ).with_company(dest_company)
            for move in self.move_ids:
                move_lines = move.move_line_ids.filtered(lambda x: x.quantity > 0)
                # To identify the correct move to write to,
                # use both the SO-PO link and the intercompany_picking_id link
                po_move_pending = (
                    move.sale_line_id.auto_purchase_line_id.move_ids.filtered(
                        lambda x, ic_pick=dest_picking: x.picking_id == ic_pick
                        and x.state not in ["done", "cancel"]
                    )
                )
                po_move_lines = po_move_pending.move_line_ids
                # Don’t raise an error
                # if there are no move_line_ids and the location is transit.
                # In vendor locations, reservations are bypassed,
                # but in transit locations,
                # we need to create the move lines to assign lots/serials.
                if not po_move_pending or (
                    po_move_lines and move.location_dest_id.usage != "transit"
                ):
                    raise UserError(
                        _(
                            "There's no corresponding line in PO %(po)s for assigning "
                            "qty from %(pick_name)s for product %(product)s"
                        )
                        % (
                            {
                                "po": purchase.name,
                                "pick_name": self.name,
                                "product": move.product_id.display_name,
                            }
                        )
                    )
                move_line_diff = len(move_lines) - len(po_move_lines)
                # generate new move lines if needed
                # example: In purchase order of C1, we have 2 move lines
                # and in reception of C2,
                # we have 3 move lines(with lot or serial number)
                # then we need to create 1 more move line in purchase order of C1
                if move_line_diff > 0:
                    new_move_line_vals = []
                    for _index in range(move_line_diff):
                        vals = po_move_pending._prepare_move_line_vals()
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
                    po_move_lines[len(move_lines) :].unlink()
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
            if dest_company.sync_picking and self.state == "done":
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
        note = _(
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
                or SUPERUSER_ID,
            ),
        )

    def _is_intercompany_reception(self):
        """
        Check if the picking is an inter-company reception.
        :return: bool
        """
        return (
            self.location_id.usage in ["supplier", "transit"]
            and self.purchase_id.sudo().intercompany_sale_order_id
        )

    def _is_intercompany_delivery(self):
        """
        Check if the picking is an inter-company delivery.
        :return: bool
        """
        return (
            self.location_dest_id.usage in ["customer", "transit"]
            and self.sale_id.sudo().auto_purchase_order_id
        )
