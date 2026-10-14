# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form

from .common import TestPurchaseSaleInterCompanyCommon


class TestPurchaseSaleInterCompany(TestPurchaseSaleInterCompanyCommon):
    def test_purchase_sale_inter_company(self):
        self.purchase_company_a.notes = "Test note"
        sale = self._approve_po()
        self.assertEqual(len(sale), 1)
        self.assertEqual(sale.state, "sale")
        self.assertEqual(sale.partner_id, self.partner_company_a)
        self.assertEqual(len(sale.order_line), len(self.purchase_company_a.order_line))
        self.assertEqual(sale.order_line.product_id, self.product)
        self.assertEqual(str(sale.note), "<p>Test note</p>")

    def test_not_auto_validate(self):
        self.company_b.sale_auto_validation = False
        sale = self._approve_po()
        self.assertEqual(sale.state, "draft")

    # TODO FIXME
    def xxtest_date_planned(self):
        # Install sale_order_dates module
        module = self.env["ir.module.module"].search(
            [("name", "=", "sale_order_dates")]
        )
        if not module:
            return False
        module.button_install()
        self.purchase_company_a.date_planned = "2070-12-31"
        sale = self._approve_po()
        self.assertEqual(sale.requested_date, "2070-12-31")

    def test_raise_product_access(self):
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.active = True
        # if product_multi_company is installed
        if "company_ids" in self.env["product.template"]._fields:
            self.product.company_ids = [Command.set([self.company_a.id])]
        self.product.company_id = self.company_a
        with self.assertRaisesRegex(
            UserError,
            f"You cannot create SO from PO because product '{self.product.name}' is "
            "not intercompany",
        ):
            self._approve_po()

    def test_raise_currency(self):
        currency = self.env.ref("base.EUR")
        self.purchase_company_a.currency_id = currency
        with self.assertRaisesRegex(
            UserError,
            "You cannot create SO from PO because sale price list currency is "
            "different than purchase price list currency.",
        ):
            self._approve_po()

    def test_purchase_invoice_relation(self):
        self.partner_company_a.company_id = False
        self.partner_company_b.company_id = False
        sale = self._approve_po()
        sale_invoice = sale._create_invoices()[0]
        sale_invoice.action_post()
        self.assertEqual(len(self.purchase_company_a.invoice_ids), 1)
        self.assertEqual(
            self.purchase_company_a.invoice_ids.auto_invoice_id,
            sale_invoice,
        )
        self.assertEqual(len(self.purchase_company_a.order_line.invoice_lines), 1)
        self.assertEqual(self.purchase_company_a.order_line.qty_invoiced, 3)

    def test_cancel(self):
        self.company_b.sale_auto_validation = False
        sale = self._approve_po()
        self.assertEqual(self.purchase_company_a.partner_ref, sale.name)
        self.purchase_company_a.with_user(self.user_company_a).button_cancel()
        self.assertFalse(self.purchase_company_a.partner_ref)
        self.assertEqual(sale.state, "cancel")

    def test_cancel_confirmed_po_so(self):
        self.company_b.sale_auto_validation = True
        sale = self._approve_po()
        self.purchase_company_a.with_user(self.user_company_a).button_cancel()
        self.assertEqual(sale.state, "cancel")

    def test_so_change_price(self):
        self.company_b.sale_auto_validation = False
        sale = self._approve_po()
        sale.order_line.price_unit = 10
        sale.action_confirm()
        self.assertEqual(self.purchase_company_a.order_line.price_unit, 10)

    def test_so_change_price_with_discount(self):
        self.company_b.sale_auto_validation = False
        sale = self._approve_po()
        sale.order_line.price_unit = 100
        sale.order_line.discount = 10
        sale.action_confirm()
        self.assertEqual(self.purchase_company_a.order_line.price_unit, 90.0)

    def test_po_with_contact_as_partner(self):
        contact = self.env["res.partner"].create(
            {"name": "Test contact", "parent_id": self.partner_company_b.id}
        )
        self.purchase_company_a = self._create_purchase_order(contact)
        sale = self._approve_po()
        self.assertEqual(len(sale), 1)
        self.assertEqual(sale.state, "sale")
        self.assertEqual(sale.partner_id, self.partner_company_a)

    def test_update_open_sale_order(self):
        """
        When the purchase user request extra product, the sale order gets synched if
        it's open.
        """
        self.company_b.sale_auto_validation = False
        purchase = self.purchase_company_a
        sale = self._approve_po()
        sale.action_confirm()
        # Now we add an extra product to the PO and it will show up in the SO
        po_form = Form(purchase)
        with po_form.order_line.new() as line:
            line.product_id = self.service_product_2
            line.product_qty = 6
        po_form.save()
        # It's synched and the values match
        synched_order_line = sale.order_line.filtered(
            lambda x: x.product_id == self.service_product_2
        )
        self.assertTrue(
            bool(synched_order_line),
            "The line should have been created in the sale order",
        )
        self.assertEqual(
            synched_order_line.product_uom_qty,
            6,
            "The quantity should be equal to the one set in the purchase order",
        )
        # The quantity is synched as well
        purchase_line = purchase.order_line.filtered(
            lambda x: x.product_id == self.service_product_2
        ).sudo()
        purchase_line.product_qty = 8
        self.assertEqual(
            synched_order_line.product_uom_qty,
            8,
            "The quantity should be equal to the one set in the purchase order",
        )
        # Let's decrease the quantity
        purchase_line.product_qty = 3
        self.assertEqual(
            synched_order_line.product_uom_qty,
            3,
            "The quantity should decrease as it was in the purchase order",
        )

    def test_default_intercompany_sale_user_id(self):
        """
        When the intercompany_sale_user_id is not set, the current user that creates the
        purchase order is used, this impacts the salesperson value on the sale order.
        Following the _compute_user_id method on sale.order model, if there is no
        salesperson set, the salesperson will be the user set on the Sale's customer,
        or customer's company, or the current user if he is a salesman.
        """
        self.company_b.intercompany_sale_user_id = False
        self.company_b.sale_auto_validation = False
        sale = self._approve_po()
        self.assertEqual(sale.create_uid, self.user_company_a)
        self.assertNotEqual(sale.user_id, self.user_company_b)
        expected_salesperson = (
            sale.partner_id.user_id
            or sale.partner_id.parent_id.user_id
            or (
                self.user_company_a
                if self.user_company_a.has_group("sales_team.group_sale_manager")
                else False
            )
        )
        self.assertNotEqual(sale.user_id, expected_salesperson)

    def test_sale_order_line_note_sync(self):
        """
        When a purchase order line has a note, it should be copied to the sale order
        line.
        """
        self.purchase_company_a.order_line = [
            (0, 0, {"name": "Test Note", "display_type": "line_note", "product_qty": 0})
        ]
        sale = self._approve_po()
        self.assertEqual(
            sale.order_line.filtered(lambda x: x.display_type == "line_note").name,
            "Test Note",
        )

    def test_cannot_modify_pol_of_related_so_is_cancel(self):
        """
        When the related sale order is cancel, the purchase order lines cannot be
        created or modified.
        """
        self.company_b.sale_auto_validation = False
        sale = self._approve_po()
        sale.action_confirm()
        purchase_line = self.purchase_company_a.order_line
        sale._action_cancel()
        with self.assertRaisesRegex(
            UserError,
            f"The generated sale orders with reference {sale.name} can't be modified. "
            "They're either unconfirmed or locked for modifications.",
        ):
            purchase_line[0].product_qty = 5
        with self.assertRaisesRegex(
            UserError,
            "You can't change this purchase order as the corresponding sale is "
            f"{sale.state}",
        ):
            self.env["purchase.order.line"].create(
                {
                    "order_id": self.purchase_company_a.id,
                    "product_id": self.service_product_2.id,
                    "product_qty": 5,
                    "name": "Test",
                }
            )
        sale.action_draft()
        sale.action_confirm()
        purchase_line[0].product_qty = 5
        self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_company_a.id,
                "product_id": self.service_product_2.id,
                "product_qty": 5,
                "name": "Test",
            }
        )

    def test_delivery_address_different_company(self):
        """
        When a purchase order has a delivery address with a different company_id
        than the destination company, the company_id should be cleared to avoid
        validation errors when creating the inter-company sale order.
        """
        delivery_address = self.env["res.partner"].create(
            {
                "name": "Delivery Address Company A",
                "company_id": self.company_a.id,
            }
        )
        purchase = self._create_purchase_order(self.partner_company_b)
        purchase.dest_address_id = delivery_address
        sale = self._approve_po(purchase)
        self.assertEqual(len(sale), 1)
        self.assertEqual(sale.state, "sale")
        self.assertEqual(sale.partner_shipping_id, delivery_address)
        self.assertFalse(sale.partner_shipping_id.company_id)

    def test_tax_exclude(self):
        """
        When the tax configuration is different between the two companies,
        the purchase order must keep the same total as the sale order.
        Company A has tax included prices
        Company B has tax excluded prices
        """
        self.company_b.sale_auto_validation = False
        # set the price_include_override to force the tax computation
        self.tax_company_a.write(
            {"price_include_override": "tax_included", "type_tax_use": "purchase"}
        )
        self.tax_company_b.write(
            {"price_include_override": "tax_excluded", "type_tax_use": "sale"}
        )
        self.product.with_company(self.company_a).supplier_taxes_id = [
            Command.link(self.tax_company_a.id)
        ]
        self.product.with_company(self.company_b).taxes_id = [
            Command.link(self.tax_company_b.id)
        ]
        self.purchase_company_a.order_line.taxes_id = [
            Command.set(self.tax_company_a.ids)
        ]

        sale = self._approve_po()
        self.assertEqual(sale.order_line.tax_id, self.tax_company_b)
        sale.order_line.price_unit = 150.0
        sale.action_confirm()
        # the quantity is 3, so 150 * 3 = 450
        self.assertAlmostEqual(sale.amount_untaxed, 450.0, places=0)
        self.assertAlmostEqual(sale.amount_total, 495.0, places=0)
        self.assertAlmostEqual(
            self.purchase_company_a.order_line.price_unit, 165.0, places=0
        )
        self.assertAlmostEqual(self.purchase_company_a.amount_untaxed, 450.0, places=0)
        self.assertAlmostEqual(self.purchase_company_a.amount_total, 495.0, places=0)

    def test_tax_include(self):
        """
        When the tax configuration is different between the two companies,
        the purchase order must keep the same total as the sale order.
        Company A has tax excluded prices
        Company B has tax included prices
        """
        self.company_b.sale_auto_validation = False
        # set the price_include_override to force the tax computation
        self.tax_company_a.write(
            {"price_include_override": "tax_excluded", "type_tax_use": "purchase"}
        )
        self.tax_company_b.write(
            {"price_include_override": "tax_included", "type_tax_use": "sale"}
        )
        self.product.with_company(self.company_a).supplier_taxes_id = [
            Command.link(self.tax_company_a.id)
        ]
        self.product.with_company(self.company_b).taxes_id = [
            Command.link(self.tax_company_b.id)
        ]
        self.purchase_company_a.order_line.taxes_id = [
            Command.set(self.tax_company_a.ids)
        ]
        sale = self._approve_po()
        self.assertEqual(sale.order_line.tax_id, self.tax_company_b)
        sale.order_line.price_unit = 150.0
        sale.action_confirm()
        # the quantity is 3, so 150 * 3 = 450
        self.assertAlmostEqual(sale.amount_untaxed, 409, places=0)
        self.assertAlmostEqual(sale.amount_total, 450.0, places=0)
        self.assertAlmostEqual(
            self.purchase_company_a.order_line.price_unit, 136.0, places=0
        )
        self.assertAlmostEqual(self.purchase_company_a.amount_untaxed, 409, places=0)
        self.assertAlmostEqual(self.purchase_company_a.amount_total, 450.0, places=0)
