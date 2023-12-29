# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    intercompany_sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        compute="_compute_intercompany_sale_order_id",
        compute_sudo=True,
    )

    def _compute_intercompany_sale_order_id(self):
        """A One2many would be simpler, but the record rules make unaccesible for
        regular users so the logic doesn't work properly"""
        ids_dict_list = self.env["sale.order"].search_read(
            [("auto_purchase_order_id", "in", self.ids)],
            ["id", "auto_purchase_order_id"],
        )
        ids_dict = {d["auto_purchase_order_id"][0]: d["id"] for d in ids_dict_list}
        for order in self:
            order.intercompany_sale_order_id = ids_dict.get(order.id, False)

    def button_approve(self, force=False):
        """Generate inter company sale order base on conditions."""
        res = super().button_approve(force)
        for purchase_order in self.sudo():
            # get the company from partner then trigger action of
            # intercompany relation
            dest_company = (
                purchase_order.partner_id.commercial_partner_id.ref_company_ids
            )
            if dest_company and dest_company.so_from_po:
                purchase_order.with_company(
                    dest_company.id
                )._inter_company_create_sale_order(dest_company)
        return res

    def _get_user_domain(self, dest_company):
        self.ensure_one()
        group_purchase_user = self.env.ref("purchase.group_purchase_user")
        return [
            ("id", "!=", 1),
            ("company_id", "=", dest_company.id),
            ("id", "in", group_purchase_user.users.ids),
        ]

    def _check_intercompany_product(self, dest_company):
        domain = self._get_user_domain(dest_company)
        dest_user = self.env["res.users"].search(domain, limit=1)
        if dest_user:
            for purchase_line in self.order_line:
                if (
                    purchase_line.product_id.company_id
                    and purchase_line.product_id.company_id not in dest_user.company_ids
                ):
                    raise UserError(
                        _(
                            "You cannot create SO from PO because product '%s' "
                            "is not intercompany"
                        )
                        % purchase_line.product_id.name
                    )

    def _inter_company_create_sale_order(self, dest_company):
        """Create a Sale Order from the current PO (self)
        Note : In this method, reading the current PO is done as sudo,
        and the creation of the derived
        SO as intercompany_user, minimizing the access right required
        for the trigger user.
        :param dest_company : the company of the created PO
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        # Check intercompany user
        intercompany_user = dest_company.intercompany_sale_user_id
        if not intercompany_user:
            intercompany_user = self.env.user
        # check intercompany product
        self._check_intercompany_product(dest_company)
        # Accessing to selling partner with selling user, so data like
        # property_account_position can be retrieved
        company_partner = self.company_id.partner_id
        # check pricelist currency should be same with PO/SO document
        if self.currency_id.id != (
            company_partner.property_product_pricelist.currency_id.id
        ):
            raise UserError(
                _(
                    "You cannot create SO from PO because "
                    "sale price list currency is different than "
                    "purchase price list currency."
                )
            )
        # create the SO and generate its lines from the PO lines
        sale_order_data = self._prepare_sale_order_data(
            self.name, company_partner, dest_company, self.dest_address_id
        )
        sale_order = (
            self.env["sale.order"]
            .with_user(intercompany_user.id)
            .sudo()
            .create(sale_order_data)
        )
        for purchase_line in self.order_line:
            sale_line_data = self._prepare_sale_order_line_data(
                purchase_line, dest_company, sale_order
            )
            self.env["sale.order.line"].with_user(intercompany_user.id).sudo().create(
                sale_line_data
            )
        # write supplier reference field on PO
        if not self.partner_ref:
            self.partner_ref = sale_order.name
        # Validation of sale order
        if dest_company.sale_auto_validation:
            sale_order.with_user(intercompany_user.id).sudo().action_confirm()

    def _prepare_sale_order_data(
        self, name, partner, dest_company, direct_delivery_address
    ):
        """Generate the Sale Order values from the PO
        :param name : the origin client reference
        :rtype name : string
        :param partner : the partner reprenseting the company
        :rtype partner : res.partner record
        :param dest_company : the company of the created SO
        :rtype dest_company : res.company record
        :param direct_delivery_address : the address of the SO
        :rtype direct_delivery_address : res.partner record
        """
        self.ensure_one()
        delivery_address = (
            direct_delivery_address
            or self.picking_type_id.warehouse_id.partner_id
            or False
        )
        new_order = self.env["sale.order"].new(
            {
                "company_id": dest_company.id,
                "client_order_ref": name,
                "partner_id": partner.id,
                "date_order": self.date_approve,
                "auto_purchase_order_id": self.id,
            }
        )
        for onchange_method in new_order._onchange_methods["partner_id"]:
            onchange_method(new_order)
        new_order.user_id = False
        if delivery_address:
            new_order.partner_shipping_id = delivery_address
        if self.notes:
            new_order.note = self.notes
        if "warehouse_id" in new_order:
            new_order.warehouse_id = (
                dest_company.warehouse_id.company_id == dest_company
                and dest_company.warehouse_id
                or False
            )
        new_order.commitment_date = self.date_planned
        return new_order._convert_to_write(new_order._cache)

    def _prepare_sale_order_line_data(self, purchase_line, dest_company, sale_order):
        """Generate the Sale Order Line values from the PO line
        :param purchase_line : the origin Purchase Order Line
        :rtype purchase_line : purchase.order.line record
        :param dest_company : the company of the created SO
        :rtype dest_company : res.company record
        :param sale_order : the Sale Order
        """
        new_line = self.env["sale.order.line"].new(
            {
                "order_id": sale_order.id,
                "product_id": purchase_line.product_id.id,
                "product_uom": purchase_line.product_uom.id,
                "product_uom_qty": purchase_line.product_qty,
                "auto_purchase_line_id": purchase_line.id,
                "display_type": purchase_line.display_type,
            }
        )
        for onchange_method in new_line._onchange_methods["product_id"]:
            onchange_method(new_line)
        new_line.update({"product_uom": purchase_line.product_uom.id})
        if new_line.display_type in ["line_section", "line_note"]:
            new_line.update({"name": purchase_line.name})
        return new_line._convert_to_write(new_line._cache)

    def button_cancel(self):
        sale_orders = (
            self.env["sale.order"]
            .sudo()
            .search([("auto_purchase_order_id", "in", self.ids)])
        )
        for so in sale_orders:
            if so.state not in ["draft", "sent", "cancel"]:
                raise UserError(_("You can't cancel an order that is %s") % so.state)
        sale_orders.action_cancel()
        self.write({"partner_ref": False})
        return super().button_cancel()


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
            for purchase_line in lines.filtered(lambda x: x.order_id == order):
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
                        for line in sale_lines.filtered(lambda x: x.order_id == sale)
                    ]
                }
            )
        for line in sale_lines:
            # Trigger line changes (e.g.: pricelist recalculation)
            # TBE: onchage_helper could fit better here
            line._onchange_product_uom_qty()
        return res
