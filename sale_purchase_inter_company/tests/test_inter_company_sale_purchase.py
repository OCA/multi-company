# Copyright 2023 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
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
    def _create_sale_order(cls, partner):
        so = Form(cls.env["sale.order"])
        so.company_id = cls.company_a
        so.partner_id = partner

        cls.product.invoice_policy = "order"

        with so.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_uom_qty = 3.0
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        return so.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # no job: avoid issue if account_invoice_inter_company_queued is installed
        cls.env = cls.env(context={"test_queue_job_no_delay": 1})

        cls.product = cls.env.ref(
            "account_invoice_inter_company.product_consultant_multi_company"
        )
        cls.product.purchase_method = "purchase"

        if "company_ids" in cls.env["res.partner"]._fields:
            # We have to do that because the default method added a company
            cls.partner_company_a.company_ids = [(6, 0, cls.company_a.ids)]
            cls.partner_company_b.company_ids = [(6, 0, cls.company_b.ids)]

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

        # Configure pricelist to USD
        cls.env["product.pricelist"].sudo().search([]).write(
            {"currency_id": cls.env.ref("base.USD").id}
        )

    def _confirm_so(self):
        """Confirm the SO in company A and return the related purchase of Company B"""
        self.sale_company_a.with_user(self.user_company_a).action_confirm()
        return (
            self.env["purchase.order"]
            .with_user(self.user_company_b)
            .search([("auto_sale_order_id", "=", self.sale_company_a.id)])
        )

    def test_sale_purchase_inter_company(self):
        self.sale_company_a.note = "Test note"
        purchase = self._confirm_so()
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, "purchase")
        self.assertEqual(purchase.partner_id, self.partner_company_a)
        self.assertEqual(len(purchase.order_line), len(self.sale_company_a.order_line))
        self.assertEqual(purchase.order_line.product_id, self.product)
        self.assertEqual(str(purchase.notes), "<p>Test note</p>")

    def test_not_auto_validate(self):
        self.company_b.purchase_auto_validation = False
        purchase = self._confirm_so()
        self.assertEqual(purchase.state, "draft")

    def test_date_planned(self):
        self.sale_company_a.commitment_date = "2070-12-31"
        purchase = self._confirm_so()
        self.assertEqual(str(purchase.date_planned.date()), "2070-12-31")

    def test_raise_product_access(self):
        product_rule = self.env.ref("product.product_comp_rule")
        product_rule.active = True
        # if product_multi_company is installed
        if "company_ids" in self.env["product.template"]._fields:
            self.product.company_ids = [(6, 0, [self.company_a.id])]
        self.product.company_id = self.company_a
        with self.assertRaises(UserError):
            self._confirm_so()

    def test_raise_currency(self):
        currency = self.env.ref("base.EUR")
        self.sale_company_a.pricelist_id.currency_id = currency
        with self.assertRaises(UserError):
            self._confirm_so()

    def test_sale_invoice_relation(self):
        self.partner_company_a.company_id = False
        self.partner_company_b.company_id = False
        purchase = self._confirm_so()
        purchase.action_create_invoice()
        purchase_invoice = purchase.invoice_ids[0]
        purchase_invoice.invoice_date = fields.Datetime.now()
        purchase_invoice.action_post()
        self.assertEqual(len(self.sale_company_a.invoice_ids), 1)
        self.assertEqual(
            self.sale_company_a.invoice_ids.auto_invoice_id,
            purchase_invoice,
        )
        self.assertEqual(len(self.sale_company_a.order_line.invoice_lines), 1)
        self.assertEqual(self.sale_company_a.order_line.qty_invoiced, 3)

    def test_cancel(self):
        self.company_b.purchase_auto_validation = False
        purchase = self._confirm_so()
        self.assertEqual(self.sale_company_a.client_order_ref, purchase.name)
        self.sale_company_a.with_user(self.user_company_a).action_cancel()
        self.assertFalse(self.sale_company_a.client_order_ref)
        self.assertEqual(purchase.state, "cancel")

    def test_cancel_confirmed_so_po(self):
        self.company_b.purchase_auto_validation = True
        self._confirm_so()
        with self.assertRaises(UserError):
            self.sale_company_a.with_user(self.user_company_a).action_cancel()

    def test_so_change_price(self):
        self.sale_company_a.order_line.price_unit = 10
        purchase = self._confirm_so()
        purchase.button_approve()
        self.assertEqual(purchase.order_line.price_unit, 10)

    def test_so_with_contact_as_partner(self):
        contact = self.env["res.partner"].create(
            {"name": "Test contact", "parent_id": self.partner_company_b.id}
        )
        self.sale_company_a = self._create_sale_order(contact)
        purchase = self._confirm_so()
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, "purchase")
        self.assertEqual(purchase.partner_id, self.partner_company_a)

    def test_sale_purchase_with_purchase_sale_inter_company_installed(self):
        # Install purchase_sale_inter_company module
        module = self.env["ir.module.module"].search(
            [("name", "=", "purchase_sale_inter_company")]
        )
        if not module:
            return False
        module.button_install()
        purchase = self._confirm_so()
        so = self.env["sale.order"].search(
            [("auto_purchase_order_id", "=", purchase.id)]
        )
        self.assertEqual(len(so), 0)
