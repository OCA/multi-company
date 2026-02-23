# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import config, float_compare


class Rma(models.Model):
    _inherit = "rma"

    intercompany_rma_id = fields.Many2one(
        comodel_name="rma",
        string="Intercompany RMA",
        readonly=True,
        copy=False,
    )
    intercompany_origin_rma_id = fields.Many2one(
        comodel_name="rma",
        string="Intercompany Origin RMA",
        readonly=True,
        copy=False,
    )

    def _get_location_final(self):
        if self.sudo().intercompany_origin_rma_id:
            return self.env.ref("stock.stock_location_inter_company")
        return super()._get_location_final()

    def _get_intercompany_sale_line(self):
        self.ensure_one()
        return self.move_id.purchase_line_id.intercompany_sale_line_id

    def _get_intercompany_origin_sale_line(self):
        self.ensure_one()
        return self.move_id.sale_line_id.auto_purchase_line_id.sudo().sale_line_id

    def _create_common_intercompany_rma_from_sale_order_line(self, sol):
        """Process that creates an RMA based on the sales order line
        (Company A or Company B).
        """
        self.ensure_one()
        dp = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        qty = self.product_uom_qty
        # Create the RMA based on the corresponding sales order
        res = sol.sudo().order_id.action_create_rma()
        # We need to use sudo() because the user likely doesn't have access
        # to the other company or hasn't selected it
        wizard = self.env[res["res_model"]].browse(res["res_id"]).sudo()
        # Set all lines with a quantity to 0
        wizard.line_ids.quantity = 0
        # Select the appropriate line and enter the necessary data
        wizard_line = wizard.line_ids.filtered(lambda x, sol=sol: x.sale_line_id == sol)
        # rma_sale_lot compatibility
        if (
            "lot_id" in self._fields
            and self.lot_id
            and "lot_id" in wizard.line_ids._fields
        ):
            wizard_lot_line = wizard_line.filtered(
                lambda x, lot=self.lot_id: x.lot_id == lot
            )
            if not wizard_lot_line:
                # Support for use cases where the related sales order has other lots
                available_lines = wizard_line.filtered(
                    lambda x, qty=qty: float_compare(
                        x.allowed_quantity,
                        qty,
                        precision_digits=dp,
                    )
                    >= 0
                )
                wizard_line = fields.first(available_lines)
            else:
                wizard_line = wizard_lot_line
        # We do not proceed if no lines have been found
        if not wizard_line:
            return
        wizard_line.operation_id = self.operation_id
        wizard_line.quantity = qty
        return wizard.create_rma()

    def _create_intercompany_rma_from_sale_order_line(self):
        """Process that creates an RMA based on the sales order line (Company A)."""
        self.ensure_one()
        sol = self._get_intercompany_sale_line()
        if self.intercompany_rma_id or not sol:
            return
        new_rma = self._create_common_intercompany_rma_from_sale_order_line(sol)
        if new_rma:
            new_rma.intercompany_origin_rma_id = self
            self.intercompany_rma_id = new_rma

    def _create_intercompany_origin_rma_from_sale_order_line(self):
        """Process that creates an RMA based on the sales order line (Company B)."""
        self.ensure_one()
        sol = self._get_intercompany_origin_sale_line()
        if self.intercompany_origin_rma_id or not sol:
            return
        new_rma = self._create_common_intercompany_rma_from_sale_order_line(sol)
        if new_rma:
            new_rma.intercompany_rma_id = self
            self.intercompany_origin_rma_id = new_rma

    def _create_intercompany_rma_from_move(self):
        """Process that creates an RMA based on another one (from a stock move)."""
        if self.env.context.get("skip_intercompany_rma_from_move"):
            return
        move_rma = self.move_id.rma_id
        if self.intercompany_rma_id or not move_rma:
            return
        rma_orig = move_rma.intercompany_origin_rma_id or move_rma.intercompany_rma_id
        if move_rma and not rma_orig:
            return
        # Create RMA from action
        # Define a specific context to prevent recursion
        res = rma_orig.with_context(
            skip_intercompany_rma_from_move=True
        ).action_create_rma()
        wizard = (
            self.env[res["res_model"]]
            .with_context(**res["context"])
            .create(
                {
                    "operation_id": self.operation_id.id,
                }
            )
        )
        new_rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        new_rma.intercompany_origin_rma_id = self
        self.intercompany_rma_id = new_rma

    def _create_intercompany_rma(self):
        for item in self.filtered(lambda x: not x.intercompany_rma_id):
            item._create_intercompany_rma_from_sale_order_line()
            item._create_intercompany_origin_rma_from_sale_order_line()
            item._create_intercompany_rma_from_move()
            new_rma = item.intercompany_rma_id.sudo()
            if not new_rma:
                continue
            if new_rma.state == "draft":
                new_rma.action_confirm()

    def _get_intercompany_rmas(self):
        intercompany_rmas = self.mapped("intercompany_rma_id").sudo()
        intercompany_rmas += self.mapped("intercompany_origin_rma_id").sudo()
        return intercompany_rmas

    def action_confirm(self):
        self._create_intercompany_rma()
        res = super().action_confirm()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_confirm = intercompany_rmas.filtered(
            lambda x: x.state != "confirmed"
        )
        if intercompany_rmas_to_confirm:
            intercompany_rmas_to_confirm.action_confirm()
        return res

    def action_cancel(self):
        """Perform the same action in the intercompany RMAs."""
        res = super().action_cancel()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_cancel = intercompany_rmas.filtered(
            lambda x: x.state != "cancelled"
        )
        if intercompany_rmas_to_cancel:
            intercompany_rmas_to_cancel.action_cancel()
        return res

    def action_draft(self):
        """Perform the same action in the intercompany RMAs."""
        res = super().action_draft()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_draft = intercompany_rmas.filtered(
            lambda x: x.state != "draft"
        )
        if intercompany_rmas_to_draft:
            intercompany_rmas_to_draft.action_draft()
        return res

    def create_replace(self, scheduled_date, warehouse, product, qty, uom):
        """Perform the same action in the intercompany RMAs."""
        res = super().create_replace(
            scheduled_date=scheduled_date,
            warehouse=warehouse,
            product=product,
            qty=qty,
            uom=uom,
        )
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_replace = intercompany_rmas.filtered(
            lambda x: x.can_be_replaced
            and x.state not in ("waiting_replacement", "replaced")
        )
        for rma in intercompany_rmas_to_replace:
            # It is important to use the right warehouse, the one belonging
            # to the right company
            rma_warehouse_to_replace = (
                warehouse
                if warehouse.company_id == rma.company_id
                else rma.warehouse_id
            )
            rma.create_replace(
                scheduled_date=scheduled_date,
                warehouse=rma_warehouse_to_replace,
                product=product,
                qty=qty,
                uom=uom,
            )
        return res

    def create_return(self, scheduled_date, qty=None, uom=None):
        """Perform the same action in the intercompany RMAs."""
        res = super().create_return(scheduled_date=scheduled_date, qty=qty, uom=uom)
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_return = intercompany_rmas.filtered(
            lambda x: x.can_be_returned
        )
        if intercompany_rmas_to_return:
            intercompany_rmas_to_return.create_return(scheduled_date, qty, uom)
        return res

    def action_refund(self):
        """Perform the same action in the intercompany RMAs."""
        res = super().action_refund()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_refund = intercompany_rmas.filtered(
            lambda x: x.can_be_refunded
        )
        if intercompany_rmas_to_refund:
            intercompany_rmas_to_refund.action_refund()
        return res

    def action_refund_without_invoice(self):
        """Perform the same action in the intercompany RMAs."""
        res = super().action_refund_without_invoice()
        intercompany_rmas = self._get_intercompany_rmas()
        intercompany_rmas_to_refund = intercompany_rmas.filtered(
            lambda x: x.can_be_refunded
        )
        if intercompany_rmas_to_refund:
            intercompany_rmas_to_refund.action_refund_without_invoice()
        return res

    def _sync_intercompany_fields(self):
        return ["operation_id", "lot_id"]

    def _sync_intercompany_data(self, vals):
        """Some data must be synchronized, for example, operation_id."""
        test_condition = not config["test_enable"] or (
            config["test_enable"] and self.env.context.get("test_rma_inter_company")
        )
        if not test_condition or self.env.context.get("skip_rma_sync_intercompany"):
            return
        intercompany_rmas = self._get_intercompany_rmas()
        if not intercompany_rmas:
            return
        new_vals = {}
        for f_name in self._sync_intercompany_fields():
            if f_name not in vals.keys():
                continue
            f_value = fields.first(self)[f_name]
            if f_value and self._fields.get(f_name).type == "many2one":
                new_vals[f_name] = f_value.id
            else:
                new_vals[f_name] = f_value
        if new_vals:
            intercompany_rmas.with_context(skip_rma_sync_intercompany=True).write(
                new_vals
            )

    def write(self, vals):
        res = super().write(vals)
        self._sync_intercompany_data(vals)
        return res
