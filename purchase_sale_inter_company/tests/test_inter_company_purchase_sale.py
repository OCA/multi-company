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
    def _create_purchase_order(cls, partner, products=None):
        if not products:
            products = [None]

        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        cls.product.invoice_policy = "order"

        for product in products:
            with po.order_line.new() as line_form:
                line_form.product_id = product or cls.product
                line_form.product_qty = 3.0
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
            # Intercompany contacts should not have a company set
            cls.partner_company_a.company_ids = False
            cls.partner_company_b.company_ids = False

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

        # Create account
        income_account = cls.env["account.account"].create(
            {
                "name": "test_account_income",
                "code": "987",
                "account_type": "income",
                "company_id": cls.company_b.id,
            }
        )
        expense_account = cls.env["account.account"].create(
            {
                "name": "test account_expenses",
                "code": "765",
                "account_type": "expense",
                "reconcile": True,
                "company_id": cls.company_a.id,
            }
        )
        # Create journal
        cls.env["account.journal"].create(
            {
                "name": "Customer Invoices - Test",
                "code": "TEST1",
                "type": "sale",
                "company_id": cls.company_b.id,
                "default_account_id": income_account.id,
            }
        )
        cls.env["account.journal"].create(
            {
                "name": "Vendor Bills - Test",
                "code": "TEST2",
                "type": "purchase",
                "company_id": cls.company_a.id,
                "default_account_id": expense_account.id,
            }
        )

    def _approve_po(self, purchase_to_approve=None):
        """Confirm the PO in company A and return the related sale of Company B"""
        if not purchase_to_approve:
            purchase_to_approve = self.purchase_company_a
        parnter_company = purchase_to_approve.company_id.partner_id.company_id
        assert not parnter_company, (
            "The partner should not have a company set, otherwise the "
            "intercompany_sale_order_id will not be computed properly. Current "
            f"partner company_id: {parnter_company.name}"
        )
        purchase_to_approve.with_user(self.user_company_a).button_approve()
        return (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", purchase_to_approve.id)])
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
        self.company_b.sale_auto_validation = False
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
        with self.assertRaises(UserError):
            purchase_line[0].product_qty = 5
        with self.assertRaises(UserError):
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
