# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        """Generate inter company purchase order base on conditions."""
        res = super().action_confirm()
        for sale_order in self.sudo():
            # check if 'purchase_sale_inter_company' is installed
            # that the sale order is not created from an inter company purchase order
            if (
                "auto_purchase_order_id" in self._fields
                and sale_order.auto_purchase_order_id
            ):
                continue
            # get the company from partner then trigger action of
            # intercompany relation
            dest_company = sale_order.partner_id.commercial_partner_id.ref_company_ids
            if dest_company and dest_company.po_from_so:
                sale_order.with_company(
                    dest_company.id
                )._inter_company_create_purchase_order(dest_company)
        return res

    def _get_user_domain(self, dest_company):
        self.ensure_one()
        group_sale_user = self.env.ref("sales_team.group_sale_salesman")
        return [
            ("id", "!=", 1),
            ("company_id", "=", dest_company.id),
            ("id", "in", group_sale_user.users.ids),
        ]

    def _check_intercompany_product(self, dest_company):
        domain = self._get_user_domain(dest_company)
        dest_user = self.env["res.users"].search(domain, limit=1)
        if dest_user:
            for sale_line in self.order_line:
                if (
                    sale_line.product_id.company_id
                    and sale_line.product_id.company_id not in dest_user.company_ids
                ):
                    raise UserError(
                        _(
                            "You cannot create PO from SO because product '%s' "
                            "is not intercompany"
                        )
                        % sale_line.product_id.name
                    )

    def _inter_company_create_purchase_order(self, dest_company):
        """Create a Purchase Order from the current SO (self)
        Note : In this method, reading the current SO is done as sudo,
        and the creation of the derived
        PO as intercompany_user, minimizing the access right required
        for the trigger user.
        :param dest_company : the customer company of the created SO
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        # Check intercompany user
        intercompany_user = dest_company.intercompany_purchase_user_id
        if not intercompany_user:
            intercompany_user = self.env.user
        # check intercompany product
        self._check_intercompany_product(dest_company)
        # Accessing to buying partner with buying user, so data like
        # property_account_position can be retrieved
        company_partner = self.company_id.partner_id
        # check pricelist currency should be same with SO/PO document
        if self.pricelist_id.currency_id.id != (
            company_partner.property_purchase_currency_id.id
            or self.company_id.currency_id.id
        ):
            raise UserError(
                _(
                    "You cannot create PO from SO because "
                    "purchase price list currency is different than "
                    "sale price list currency."
                )
            )
        # create the PO and generate its lines from the SO lines
        purchase_order_data = self._prepare_purchase_order_data(
            self.name, company_partner, dest_company
        )
        purchase_order = (
            self.env["purchase.order"]
            .with_user(intercompany_user.id)
            .sudo()
            .create(purchase_order_data)
        )
        for sale_line in self.order_line:
            purchase_line_data = self._prepare_purchase_order_line_data(
                sale_line, dest_company, purchase_order
            )
            purchase_line = (
                self.env["purchase.order.line"]
                .with_user(intercompany_user.id)
                .sudo()
                .create(purchase_line_data)
            )
            if sale_line.order_id.commitment_date:
                purchase_line.date_planned = sale_line.order_id.commitment_date
        # write customer reference field on SO
        if not self.client_order_ref:
            self.client_order_ref = purchase_order.name
        # Validation of purchase order
        if dest_company.purchase_auto_validation:
            purchase_order.with_user(intercompany_user.id).sudo().button_approve()

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
                "date_approve": self.date_order,
                "auto_sale_order_id": self.id,
            }
        )
        for onchange_method in new_order._onchange_methods["partner_id"]:
            onchange_method(new_order)
        new_order.user_id = False
        if self.note:
            new_order.notes = self.note
        return new_order._convert_to_write(new_order._cache)

    def _prepare_purchase_order_line_data(
        self, sale_line, dest_company, purchase_order
    ):
        """Generate the Purchase Order Line values from the SO line
        :param sale_line : the origin Sale Order Line
        :rtype sale_line : sale.order.line record
        :param dest_company : the supplier company of the created PO
        :rtype dest_company : res.company record
        :param purchase_order : the Purchase Order
        """
        new_line = self.env["purchase.order.line"].new(
            {
                "order_id": purchase_order.id,
                "product_id": sale_line.product_id.id,
                "auto_sale_line_id": sale_line.id,
                "display_type": sale_line.display_type,
            }
        )
        for onchange_method in new_line._onchange_methods["product_id"]:
            onchange_method(new_line)
        new_line.update(
            {
                "product_uom": sale_line.product_uom.id,
                "product_qty": sale_line.product_uom_qty,
            }
        )
        if new_line.display_type in ["line_section", "line_note"]:
            new_line.update({"name": sale_line.name})
        return new_line._convert_to_write(new_line._cache)

    def action_cancel(self):
        for sale_order in self:
            # check if 'purchase_sale_inter_company' is installed
            # that the sale order is not created from an inter company purchase order
            if (
                "auto_purchase_order_id" in self._fields
                and sale_order.auto_purchase_order_id
            ):
                continue
            purchase_orders = (
                self.env["purchase.order"]
                .sudo()
                .search([("auto_sale_order_id", "=", sale_order.id)])
            )
            for po in purchase_orders:
                if po.state not in ["draft", "sent", "cancel"]:
                    raise UserError(
                        _("You can't cancel an order that is %s") % po.state
                    )
            purchase_orders.button_cancel()
            self.write({"client_order_ref": False})
        return super().action_cancel()
