# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2025 Batista10
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    intercompany_purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        compute="_compute_intercompany_purchase_order_id",
        compute_sudo=True,
    )

    auto_purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Target Purchase Order",
        readonly=True,
        copy=False,
    )

    def _compute_intercompany_purchase_order_id(self):
        """Find the PO created automatically from this SO."""
        ids_dict_list = self.env["purchase.order"].search_read(
            [("auto_sale_order_id", "in", self.ids)],
            ["id", "auto_sale_order_id"],
        )
        ids_dict = {d["auto_sale_order_id"][0]: d["id"] for d in ids_dict_list}
        for order in self:
            order.intercompany_purchase_order_id = ids_dict.get(order.id, False)

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
            for sale_line in self.order_line:
                sale_line._check_intercompany_product(dest_user, dest_company)

    def action_confirm(self):
        """When confirming a SO, if the customer is another company in the system
        and the destination company has po_from_so enabled, create the mirror PO."""
        res = super().action_confirm()
        for sale in self.sudo():
            dest_company = sale.partner_id.commercial_partner_id.ref_company_ids
            if dest_company and dest_company.po_from_so:
                sale.with_company(dest_company.id)._inter_company_create_purchase_order(
                    dest_company
                )

        return res

    def _inter_company_create_purchase_order(self, dest_company):
        """Create a Purchase Order in the destination company from this SO."""
        self.ensure_one()
        intercompany_user = dest_company.intercompany_purchase_user_id or self.env.user

        # Pre-checks
        self._check_intercompany_product(dest_company)

        # The vendor of the PO will be the partner of the source company
        vendor_partner = self.company_id.partner_id

        # Currency coherence between SO and price list/destination company
        if self.currency_id.id != (
            vendor_partner.property_purchase_currency_id.id
            or dest_company.currency_id.id
        ):
            # NB: property_purchase_currency_id is not always defined;
            # it is compared with the company one if necessary
            raise UserError(
                _(
                    "You cannot create PO from SO because "
                    "purchase currency is different than sale order currency."
                )
            )

        # PO data
        po_vals = self._prepare_purchase_order_data(
            self.client_order_ref or self.name,
            vendor_partner,
            dest_company,
            self.partner_shipping_id,
        )
        purchase = (
            self.env["purchase.order"]
            .with_user(intercompany_user.id)
            .sudo()
            .create(po_vals)
        )

        # Message in the PO chat
        purchase.sudo().message_post(
            body=_(
                "This purchase order has been automatically created "
                "from an intercompany sale order (%s)."
            )
            % self.name,
            message_type="comment",
        )

        # PO lines
        for so_line in self.order_line:
            pol_vals = self._prepare_purchase_order_line_data(
                so_line, dest_company, purchase
            )
            pol = (
                self.env["purchase.order.line"]
                .with_user(intercompany_user.id)
                .sudo()
                .create(pol_vals)
            )
            # backlink to sales line
            so_line.auto_purchase_line_id = pol.id

        # Write vendor reference to SO
        if not self.client_order_ref:
            self.client_order_ref = purchase.name

        # PO validation if applicable
        if dest_company.purchase_auto_validation:
            purchase.with_user(intercompany_user.id).sudo().button_confirm()

        # Backlink to the SO
        self.auto_purchase_order_id = purchase.id

        return purchase

    def _prepare_purchase_order_data(
        self, origin_ref, vendor_partner, dest_company, shipping_address
    ):
        """Generate the PO values from the SO."""
        self.ensure_one()
        new_order = self.env["purchase.order"].new(
            {
                "company_id": dest_company.id,
                "partner_id": vendor_partner.id,
                "date_order": self.date_order,
                "origin": origin_ref,
                "auto_sale_order_id": self.id,
                "dest_address_id": shipping_address.id if shipping_address else False,
                "notes": self.note or False,
                "partner_ref": self.name,
            }
        )
        for onchange in new_order._onchange_methods.get("partner_id", []):
            onchange(new_order)
        # dates
        if self.commitment_date:
            new_order.date_planned = self.commitment_date
        return new_order._convert_to_write(new_order._cache)

    def _prepare_purchase_order_line_data(
        self, sale_line, dest_company, purchase_order
    ):
        # Create a line with essential information for onchange
        new_line = self.env["purchase.order.line"].new(
            {
                "order_id": purchase_order.id,
                "product_id": sale_line.product_id.id,
                "product_uom": sale_line.product_uom.id,
                "display_type": sale_line.display_type,
            }
        )

        # Execute onchanges so that Odoo calculates default values
        for onchange in new_line._onchange_methods.get("product_id", []):
            onchange(new_line)

        # Override the values we want from the SO
        new_line.update(
            {
                "product_qty": sale_line.product_uom_qty,
                "price_unit": sale_line.price_unit,
                "auto_sale_line_id": sale_line.id,
                "name": sale_line.name,
            }
        )

        return new_line._convert_to_write(new_line._cache)

    def action_cancel(self):
        """If we cancel the SO, cancel the mirror PO (if in editable status)."""
        purchase_orders = (
            self.env["purchase.order"]
            .sudo()
            .search([("auto_sale_order_id", "in", self.ids)])
        )
        for po in purchase_orders:
            if po.state not in ["draft", "sent", "to approve", "cancel"]:
                raise UserError(_("You can't cancel an order that is %s") % po.state)
        for po in purchase_orders:
            po.button_cancel()
        self.write({"auto_purchase_order_id": False})
        return super().action_cancel()
