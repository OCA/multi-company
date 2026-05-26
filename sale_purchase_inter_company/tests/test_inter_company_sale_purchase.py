# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Batista10
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)


class TestSalePurchaseInterCompany(TestAccountInvoiceInterCompanyBase):
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
    def _create_sale_order(cls, partner, products=None):
        if not products:
            products = [None]

        so = Form(cls.env["sale.order"])
        so.company_id = cls.company_a
        so.partner_id = partner

        cls.product.invoice_policy = "order"

        for product in products:
            with so.order_line.new() as line_form:
                line_form.product_id = product or cls.product
                line_form.product_uom_qty = 3.0
                line_form.price_unit = 450.0
        return so.save()

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

        # Configure Company B (the customer)
        cls.company_b.po_from_so = True
        cls.company_b.purchase_auto_validation = 1

        cls.intercompany_purchase_user_id = cls.user_company_b.copy()
        cls.intercompany_purchase_user_id.company_ids |= cls.company_a
        cls.company_b.intercompany_purchase_user_id = cls.intercompany_purchase_user_id

        # Configure User
        cls._configure_user(cls.user_company_a)
        cls._configure_user(cls.user_company_b)

        # Create sale order
        cls.sale_company_a = cls._create_sale_order(cls.partner_company_b)

        # Create account
        income_account = cls.env["account.account"].create(
            {
                "name": "test_account_income",
                "code": "789",
                "account_type": "income",
                "company_id": cls.company_a.id,
            }
        )
        expense_account = cls.env["account.account"].create(
            {
                "name": "test account_expenses",
                "code": "567",
                "account_type": "expense",
                "reconcile": True,
                "company_id": cls.company_b.id,
            }
        )
        # Create journal
        cls.env["account.journal"].create(
            {
                "name": "Customer Invoices - Test",
                "code": "TEST1",
                "type": "sale",
                "company_id": cls.company_a.id,
                "default_account_id": income_account.id,
            }
        )
        cls.env["account.journal"].create(
            {
                "name": "Vendor Bills - Test",
                "code": "TEST2",
                "type": "purchase",
                "company_id": cls.company_b.id,
                "default_account_id": expense_account.id,
            }
        )

    def _approve_so(self, sale_to_approve=None):
        """Confirm the SO in company A and return the related purchase of Company B"""
        if not sale_to_approve:
            sale_to_approve = self.sale_company_a
        parnter_company = sale_to_approve.company_id.partner_id.company_id
        assert not parnter_company, (
            "The partner should not have a company set, otherwise the "
            "intercompany_purchase_order_id will not be computed properly. Current "
            f"partner company_id: {parnter_company.name}"
        )
        sale_to_approve.with_user(self.user_company_a).action_confirm()
        return (
            self.env["purchase.order"]
            .with_user(self.user_company_b)
            .search([("auto_sale_order_id", "=", sale_to_approve.id)])
        )

    def test_sale_purchase_inter_company(self):
        self.sale_company_a.note = "Test note"
        purchase = self._approve_so()
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, "purchase")
        self.assertEqual(purchase.partner_id, self.partner_company_a)
        self.assertEqual(len(purchase.order_line), len(self.sale_company_a.order_line))
        self.assertEqual(purchase.order_line.product_id, self.product)
        self.assertEqual(str(purchase.notes), "<p>Test note</p>")

    def test_not_auto_validate(self):
        self.company_b.purchase_auto_validation = False
        purchase = self._approve_so()
        self.assertEqual(purchase.state, "draft")

    def test_raise_product_access(self):
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.active = True
        # if product_multi_company is installed
        if "company_ids" in self.env["product.template"]._fields:
            self.product.company_ids = [(6, 0, [self.company_a.id])]
        self.product.company_id = self.company_a
        with self.assertRaises(UserError):
            self._approve_so()

    def test_raise_currency(self):
        currency = self.env.ref("base.EUR")
        self.sale_company_a.currency_id = currency
        with self.assertRaises(UserError):
            self._approve_so()

    def test_sale_invoice_relation(self):
        self.partner_company_a.company_id = False
        self.partner_company_b.company_id = False
        purchase = self._approve_so()
        purchase_invoice_id = purchase.action_create_invoice()["res_id"]
        purchase_invoice = self.env["account.move"].browse(purchase_invoice_id)
        purchase_invoice.invoice_date = datetime.now()
        purchase_invoice.action_post()
        self.assertEqual(len(self.sale_company_a.invoice_ids), 1)
        self.assertEqual(
            self.sale_company_a.invoice_ids.auto_invoice_id,
            purchase_invoice,
        )
        self.assertEqual(len(self.sale_company_a.order_line.invoice_lines), 1)
        self.assertEqual(self.sale_company_a.order_line.qty_invoiced, 3)
