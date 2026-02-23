# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import config


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        is_rma_in_picking = any(pick._is_intercompany_rma_reception() for pick in self)
        if is_rma_in_picking:
            # We use a special context that we will use in sale.order.line
            self = self.with_context(rma_inter_company_picking_action_done=True)
        res = super()._action_done()
        self._action_done_rma_intercompany_actions()
        return res

    def _action_done_rma_intercompany_actions(self):
        test_condition = not config["test_enable"] or (
            config["test_enable"] and self.env.context.get("test_rma_inter_company")
        )
        if not test_condition:
            return
        # Auto-done RMA IN Company A
        for picking in self.filtered(
            lambda pick: pick._is_intercompany_rma_origin_reception()
        ):
            done_moves = picking.move_ids.filtered(lambda x: x.state == "done")
            rmas = done_moves.rma_receiver_ids.intercompany_origin_rma_id.sudo()
            pending_rma_reception_pickings = rmas.reception_move_id.picking_id.filtered(
                lambda x: x.state == "assigned"
            )
            if pending_rma_reception_pickings:
                pending_rma_reception_pickings.button_validate()
        # Auto-done RMA IN Company B
        for picking in self.filtered(
            lambda pick: pick._is_intercompany_rma_reception()
        ):
            done_moves = picking.move_ids.filtered(lambda x: x.state == "done")
            rmas = done_moves.rma_receiver_ids.intercompany_rma_id.sudo()
            rma_pickings = rmas.reception_move_id.picking_id
            pending_rma_reception_pickings = rma_pickings.filtered(
                lambda x: x.state == "assigned"
            )
            if pending_rma_reception_pickings:
                pending_rma_reception_pickings.button_validate()
        # Auto-done RMA OUT Company A
        for picking in self.filtered(
            lambda pick: pick._is_intercompany_origin_rma_delivery()
        ):
            rmas = picking.move_ids.rma_id.intercompany_origin_rma_id.sudo()
            rma_delivery_pickings = rmas.delivery_move_ids.picking_id
            confirmed_rma_delivery_pickings = rma_delivery_pickings.filtered(
                lambda x: x.state == "confirmed"
            )
            if confirmed_rma_delivery_pickings:
                # Tip for replace
                confirmed_rma_delivery_pickings.action_assign()
            pending_rma_delivery_pickings = rma_delivery_pickings.filtered(
                lambda x: x.state == "assigned"
            )
            if pending_rma_delivery_pickings:
                # lot compatibility to avoid error
                for (
                    sml
                ) in pending_rma_delivery_pickings.move_ids.move_line_ids.filtered(
                    lambda x: x.lot_id
                ):
                    sml.lot_id.sudo().company_id = False
                pending_rma_delivery_pickings.button_validate()
        # Auto-done RMA OUT Company B
        for picking in self.filtered(lambda pick: pick._is_intercompany_rma_delivery()):
            rmas = picking.move_ids.rma_id.intercompany_rma_id.sudo()
            rma_delivery_pickings = rmas.delivery_move_ids.picking_id
            confirmed_rma_delivery_pickings = rma_delivery_pickings.filtered(
                lambda x: x.state == "confirmed"
            )
            if confirmed_rma_delivery_pickings:
                # Tip for replace
                confirmed_rma_delivery_pickings.action_assign()
            pending_rma_delivery_pickings = rma_delivery_pickings.filtered(
                lambda x: x.state == "assigned"
            )
            if pending_rma_delivery_pickings:
                pending_rma_delivery_pickings.button_validate()

    def action_cancel(self):
        res = super().action_cancel()
        self._action_cancel_rma_intercompany_actions()
        return res

    def _action_cancel_rma_intercompany_actions(self):
        test_condition = not config["test_enable"] or (
            config["test_enable"] and self.env.context.get("test_rma_inter_company")
        )
        if not test_condition:
            return
        # Auto-cancel RMA OUT Company A
        for picking in self.filtered(
            lambda pick: pick._is_intercompany_origin_rma_delivery()
        ):
            rmas = picking.move_ids.rma_id.intercompany_origin_rma_id.sudo()
            pending_rma_delivery_pickings = rmas.delivery_move_ids.picking_id.filtered(
                lambda x: x.state not in ("done", "cancel")
            )
            if pending_rma_delivery_pickings:
                pending_rma_delivery_pickings.action_cancel()

    def _is_intercompany_rma_reception(self):
        return any(m.move_ids.rma_receiver_ids.intercompany_rma_id for m in self.sudo())

    def _is_intercompany_rma_origin_reception(self):
        return any(
            m.move_ids.rma_receiver_ids.intercompany_origin_rma_id for m in self.sudo()
        )

    def _is_intercompany_rma_delivery(self):
        return any(m.move_ids.rma_id.intercompany_rma_id for m in self.sudo())

    def _is_intercompany_origin_rma_delivery(self):
        return any(m.move_ids.rma_id.intercompany_origin_rma_id for m in self.sudo())
