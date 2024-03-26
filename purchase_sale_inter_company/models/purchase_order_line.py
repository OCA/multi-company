# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    intercompany_sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        compute="_compute_intercompany_sale_line_id",
        compute_sudo=True,
    )

    def _compute_intercompany_sale_line_id(self):
        """A One2many would be simpler, but the record rules make unaccesible for
        regular users so the logic doesn't work properly"""
        ids_dict_list = self.env["sale.order.line"].search_read(
            [("auto_purchase_line_id", "in", self.ids)], ["id", "auto_purchase_line_id"]
        )
        ids_dict = {d["auto_purchase_line_id"][0]: d["id"] for d in ids_dict_list}
        for line in self:
            line.intercompany_sale_line_id = ids_dict.get(line.id, False)

    @api.model_create_multi
    def create(self, vals_list):
        """Sync lines between an confirmed unlocked purchase and a confirmed unlocked
        sale order"""
        lines = super().create(vals_list)
        for order in lines.order_id.filtered(
            lambda x: x.state == "purchase" and x.intercompany_sale_order_id
        ):
            if order.intercompany_sale_order_id.sudo().state in {"cancel", "done"}:
                raise UserError(
                    _(
                        "You can't change this purchase order as the corresponding "
                        "sale is %(state)s",
                        state=order.state,
                    )
                )
            intercompany_user = (
                order.intercompany_sale_order_id.sudo().company_id.intercompany_sale_user_id
                or self.env.user
            )
            sale_lines = []
            for purchase_line in lines.filtered(lambda x, o=order: x.order_id == o):
                sale_lines.append(
                    order._prepare_sale_order_line_data(
                        purchase_line,
                        order.intercompany_sale_order_id.sudo().company_id,
                        order.intercompany_sale_order_id.sudo(),
                    )
                )
            self.env["sale.order.line"].with_user(intercompany_user.id).sudo().create(
                sale_lines
            )
        return lines

    @api.model
    def _get_purchase_sale_line_sync_fields(self):
        """Map purchase line fields to the synced sale line peer"""
        return {
            "product_qty": "product_uom_qty",
        }

    def write(self, vals):
        """Sync values of confirmed unlocked sales"""
        res = super().write(vals)
        sync_map = self._get_purchase_sale_line_sync_fields()
        update_vals = {
            sync_map.get(field): value
            for field, value in vals.items()
            if sync_map.get(field)
        }
        if not update_vals:
            return res
        intercompany_user = (
            self.intercompany_sale_line_id.sudo().company_id.intercompany_sale_user_id
            or self.env.user
        )
        sale_lines = self.intercompany_sale_line_id.with_user(
            intercompany_user.id
        ).sudo()
        if not sale_lines:
            return res
        closed_sale_lines = sale_lines.filtered(lambda x: x.state != "sale")
        if closed_sale_lines:
            raise UserError(
                _(
                    "The generated sale orders with reference %(orders)s can't be "
                    "modified. They're either unconfirmed or locked for modifications.",
                    orders=",".join(closed_sale_lines.order_id.mapped("name")),
                )
            )
        # Update directly the sale order so we can trigger the decreased qty exceptions
        for sale in sale_lines.order_id:
            sale.write(
                {
                    "order_line": [
                        (1, line.id, update_vals)
                        for line in sale_lines.filtered(
                            lambda x, s=sale: x.order_id == s
                        )
                    ]
                }
            )
        return res

    @api.model
    def _check_intercompany_product(self, dest_user, dest_company):
        if (
            self.product_id.company_id
            and self.product_id.company_id not in dest_user.company_ids
        ):
            raise UserError(
                _(
                    "You cannot create SO from PO because product '%s' "
                    "is not intercompany"
                )
                % self.product_id.name
            )
