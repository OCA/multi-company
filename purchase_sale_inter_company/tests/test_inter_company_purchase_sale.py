# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)


class TestPurchaseSaleInterCompany(TestAccountInvoiceInterCompanyBase):
    @classmethod
    def _configure_user(cls, user):
        for xml in [
            "account.group_account_manager",
            "base.group_partner_manager",
            "sales_team.group_sale_manager",
            "purchase.group_purchase_manager",
        ]:
            user.groups_id |= cls.env.ref(xml)

    @classmethod
    def _create_purchase_order(cls, partner):
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        cls.product.invoice_policy = "order"

        with po.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_qty = 3.0
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        return po.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # no job: avoid issue if account_invoice_inter_company_queued is installed
        cls.env = cls.env(context={"test_queue_job_no_delay": 1})

        cls.product = cls.product_consultant_multi_company
        cls.service_product_2 = cls.env["product.product"].create(
            {
                "name": "Service Product 2",
                "type": "service",
            }
        )
        # if product_multi_company is installed
        if "company_ids" in cls.env["product.template"]._fields:
            # We have to do that because the default method added a company
            cls.service_product_2.company_ids = False

        if "company_ids" in cls.env["res.partner"]._fields:
            # We have to do that because the default method added a company
            cls.partner_company_a.company_ids = [(6, 0, cls.company_a.ids)]
            cls.partner_company_b.company_ids = [(6, 0, cls.company_b.ids)]

        # Configure Company B (the supplier)
        cls.company_b.so_from_po = True
        cls.company_b.sale_auto_validation = 1

        cls.intercompany_sale_user_id = cls.user_company_b.copy()
        cls.intercompany_sale_user_id.company_ids |= cls.company_a
        cls.company_b.intercompany_sale_user_id = cls.intercompany_sale_user_id

        # Configure User
        cls._configure_user(cls.user_company_a)
        cls._configure_user(cls.user_company_b)

        # Create purchase order
        cls.purchase_company_a = cls._create_purchase_order(cls.partner_company_b)

        # Configure pricelist to USD
        cls.env["product.pricelist"].sudo().search([]).write(
            {"currency_id": cls.env.ref("base.USD").id}
        )

    def _approve_po(self):
        """Confirm the PO in company A and return the related sale of Company B"""
        self.purchase_company_a.with_user(self.user_company_a).button_approve()
        return (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", self.purchase_company_a.id)])
        )

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
            self.product.company_ids = [(6, 0, [self.company_a.id])]
        self.product.company_id = self.company_a
        with self.assertRaises(UserError):
            self._approve_po()

    def test_raise_currency(self):
        currency = self.env.ref("base.EUR")
        self.purchase_company_a.currency_id = currency
        with self.assertRaises(UserError):
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
        self._approve_po()
        with self.assertRaises(UserError):
            self.purchase_company_a.with_user(self.user_company_a).button_cancel()

    def test_so_change_price(self):
        sale = self._approve_po()
        sale.order_line.price_unit = 10
        sale.action_confirm()
        self.assertEqual(self.purchase_company_a.order_line.price_unit, 10)

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

    def test_bypass_check_when_update_locked_sale_order_with_ctx(self):
        self.intercompany_sale_user_id.groups_id += self.env.ref(
            "sale.group_auto_done_setting"
        )
        purchase = self.purchase_company_a
        sale = self._approve_po()
        # Now, the SO is in Locked state
        self.assertEqual(sale.state, "done")
        # Without `allow_update_locked_sales` ctx
        with self.assertRaisesRegex(
            UserError,
            "You can't change this purchase order as the corresponding sale"
            f" is {purchase.state}",
        ):
            purchase.order_line.create(
                [
                    {
                        "order_id": purchase.id,
                        "name": self.product.name,
                        "product_id": self.product.id,
                        "product_qty": 280,
                        "price_unit": 99,
                    },
                ]
            )
        with self.assertRaisesRegex(
            UserError,
            f"The generated sale orders with reference {sale.name} can't be "
            "modified. They're either unconfirmed or locked for modifications.",
        ):
            purchase.order_line[0].write({"product_qty": 99})
        # We can bypass the check with `allow_update_locked_sales` ctx
        purchase.order_line.with_context(allow_update_locked_sales=True).create(
            [
                {
                    "order_id": purchase.id,
                    "name": self.product.name,
                    "product_id": self.product.id,
                    "product_qty": 280,
                    "price_unit": 99,
                },
            ]
        )
        # But we still need another logic to handle on the sale order when write
        # Example:
        # https://github.com/OCA/sale-workflow/commit/3fe8ed00c046c9ef68a487eedea282ecb5415231
        with self.assertRaisesRegex(
            UserError,
            "It is forbidden to modify the following fields in a locked order:\nQuantity",
        ):
            purchase.order_line[0].with_context(allow_update_locked_sales=True).write(
                {"product_qty": 99}
            )
