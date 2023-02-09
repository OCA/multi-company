# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
            po_company = order.sudo().auto_purchase_order_id.company_id
            if not po_company.intercompany_overwrite_purchase_price:
                order.assert_intercompany_prices_equal()
            else:
                for line in order.order_line.sudo():
                    if line.auto_purchase_line_id:
                        line.auto_purchase_line_id.price_unit = line.price_unit
        res = super(SaleOrder, self).action_confirm()
        for sale_order in self.sudo():
            # Do not consider SO created from intercompany PO
            dest_company = sale_order.partner_id.ref_company_ids
            if not sale_order.auto_purchase_order_id:
                if dest_company and dest_company.po_from_so:
                    sale_order.with_context(
                        force_company=dest_company.id
                    )._inter_company_create_purchase_order(dest_company)
            if (
                sale_order.auto_purchase_order_id
                and dest_company
                and dest_company.sync_picking
            ):
                pickings = sale_order.picking_ids
                purchase_picking = sale_order.auto_purchase_order_id.sudo().picking_ids

                if len(pickings) == len(purchase_picking) == 1:
                    purchase_picking.sudo().write(
                        {"intercompany_picking_id": pickings[0].id}
                    )
                    pickings[0].write({"intercompany_picking_id": purchase_picking.id})
                if len(pickings) > 1 and len(purchase_picking) == 1:
                    # If there are `n` pickings in the sale order
                    # and one in the purchase order, split the receipt
                    assigned_moves = []
                    assigned_move_lines = []
                    for pick in pickings:
                        assigned = (
                            purchase_picking.sudo().move_ids_without_package.filtered(
                                lambda m: m.product_id.id
                                in pick.mapped("move_ids_without_package.product_id.id")
                            )
                        )
                        lines = purchase_picking.sudo().move_line_ids_without_package
                        assigned_lines = lines.filtered(
                            lambda m: m.product_id.id
                            in pick.mapped(
                                "move_line_ids_without_package.product_id.id"
                            )
                        )
                        assigned_moves.append(assigned)
                        assigned_move_lines.append(assigned_lines)

                    for i in range(len(assigned_moves)):
                        if i == 0:
                            purchase_picking.write(
                                {
                                    "move_ids_without_package": [
                                        (6, False, assigned_moves[i].ids)
                                    ],
                                    "move_line_ids_without_package": [
                                        (6, False, assigned_move_lines[i].ids)
                                    ],
                                    "intercompany_picking_id": pickings[i].id,
                                }
                            )
                            pickings[i].write(
                                {"intercompany_picking_id": purchase_picking.id}
                            )
                            purchase_picking.action_assign()
                        else:
                            new = purchase_picking.copy(
                                {
                                    "move_ids_without_package": [
                                        (6, False, assigned_moves[i].ids)
                                    ],
                                    "move_line_ids_without_package": [
                                        (6, False, assigned_move_lines[i].ids)
                                    ],
                                    "intercompany_picking_id": pickings[i].id,
                                }
                            )
                            new.action_assign()
                            pickings[i].write({"intercompany_picking_id": new.id})

        return res

    @api.multi
    def _get_user_domain(self, dest_company):
        self.ensure_one()
        group_sale_user = self.env.ref("sales_team.group_sale_salesman")
        return [
            ("id", "!=", 1),
            ("company_id", "=", dest_company.id),
            ("id", "in", group_sale_user.users.ids),
        ]

    @api.multi
    def _check_intercompany_product(self, dest_company):
        domain = self._get_user_domain(dest_company)
        dest_user = self.env["res.users"].search(domain, limit=1)
        if dest_user:
            for sale_line in self.order_line:
                try:
                    sale_line.product_id.sudo(dest_user).read(["default_code"])
                except Exception:
                    raise UserError(
                        _(
                            "You cannot create PO from SO because product '%s' "
                            "is not intercompany"
                        )
                        % sale_line.product_id.name
                    )

    @api.multi
    def _inter_company_create_purchase_order(self, dest_company):
        """Create a Purchase Order from the current SO (self)
        Note : In this method, reading the current SO is done as sudo,
        and the creation of the derived
        PO as intercompany_user, minimizing the access right required
        for the trigger user.
        :param dest_company : the company of the created SO
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        intercompany_user = dest_company.intercompany_user_id
        if intercompany_user.company_id != dest_company:
            intercompany_user.company_id = dest_company
        self._check_intercompany_product(dest_company)
        company_partner = self.company_id.partner_id
        purchase_order_data = self._prepare_purchase_order_data(
            self.name, company_partner, dest_company
        )
        purchase_order = (
            self.env["purchase.order"]
            .sudo(intercompany_user.id)
            .create(purchase_order_data)
        )
        for sale_line in self.order_line:
            purchase_line_data = self._prepare_purchase_order_line_data(
                sale_line, purchase_order
            )
            self.env["purchase.order.line"].sudo(intercompany_user.id).create(
                purchase_line_data
            )
        if not self.name:
            self.name = purchase_order.partner_ref
        # Validation of sale order
        if dest_company.purchase_auto_validation:
            purchase_order.sudo(intercompany_user.id).button_approve()

    @api.multi
    def _prepare_purchase_order_data(self, name, partner, dest_company):
        """Generate the Purchase Order values from the SO
        :param name : the origin client reference
        :rtype name : string
        :param partner : the partner reprenseting the company
        :rtype partner : res.partner record
        :param dest_company : the company of the created PO
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        new_order = self.env["purchase.order"].new(
            {
                "company_id": dest_company.id,
                "partner_ref": name,
                "partner_id": partner.id,
                "date_order": self.date_order,
                "auto_sale_order_id": self.id,
            }
        )
        for onchange_method in new_order._onchange_methods["partner_id"]:
            onchange_method(new_order)
        new_order.user_id = False
        if self.note:
            new_order.notes = self.note
        if "picking_type_id" in new_order:
            new_order.picking_type_id = (
                dest_company.po_picking_type_id.warehouse_id.company_id == dest_company
                and dest_company.po_picking_type_id
                or False
            )
        return new_order._convert_to_write(new_order._cache)

    @api.model
    def _prepare_purchase_order_line_data(self, sale_line, purchase_order):
        """Generate the Purchase Order Line values from the SO line
        :param sale_line : the origin Sale Order Line
        :rtype sale_line : sale.order.line record
        :param purchase_order : the Purchase Order
        """
        new_line = self.env["purchase.order.line"].new(
            {
                "order_id": purchase_order.id,
                "product_id": sale_line.product_id.id,
                "auto_sale_line_id": sale_line.id,
            }
        )
        for onchange_method in new_line._onchange_methods["product_id"]:
            onchange_method(new_line)
        new_line.product_uom = sale_line.product_uom.id
        new_line.product_qty = sale_line.product_uom_qty
        new_line.price_unit = sale_line.price_unit
        return new_line._convert_to_write(new_line._cache)

    @api.multi
    def action_cancel(self):
        purchase_orders = (
            self.env["purchase.order"]
            .sudo()
            .search([("auto_sale_order_id", "in", self.ids)])
        )
        for po in purchase_orders:
            if po.state not in ["draft", "sent", "cancel"]:
                raise UserError(_("You can't cancel an order that is %s") % po.state)
        if purchase_orders:
            purchase_orders.button_cancel()
        return super().action_cancel()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Source Purchase Order Line",
        readonly=True,
        copy=False,
    )
