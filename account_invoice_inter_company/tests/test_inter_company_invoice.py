# Copyright 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase


@tagged("post_install", "-at_install")
class TestAccountInvoiceInterCompanyBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_obj = cls.env["account.account"]
        cls.account_move_obj = cls.env["account.move"]
        cls.chart = cls.env["account.chart.template"].search([], limit=1)
        if not cls.chart:
            raise ValidationError(
                # translation to avoid pylint warnings
                _("No Chart of Account Template has been defined !")
            )

        cls.company_a = cls.env["res.company"].create(
            {
                "name": "Company A",
                "currency_id": cls.env.ref("base.EUR").id,
                "country_id": cls.env.ref("base.fr").id,
                "parent_id": cls.env.ref("base.main_company").id,
                "invoice_auto_validation": True,
                "intercompany_invoicing": True,
            }
        )
        cls.chart.try_loading(company=cls.company_a, install_demo=False)
        cls.partner_company_a = cls.env["res.partner"].create(
            {"name": cls.company_a.name, "is_company": True}
        )
        cls.company_a.partner_id = cls.partner_company_a
        cls.company_b = cls.env["res.company"].create(
            {
                "name": "Company B",
                "currency_id": cls.env.ref("base.EUR").id,
                "country_id": cls.env.ref("base.fr").id,
                "parent_id": cls.env.ref("base.main_company").id,
                "invoice_auto_validation": True,
                "intercompany_invoicing": True,
            }
        )
        cls.chart.try_loading(company=cls.company_b, install_demo=False)
        cls.partner_company_b = cls.env["res.partner"].create(
            {"name": cls.company_b.name, "is_company": True}
        )
        cls.child_partner_company_b = cls.env["res.partner"].create(
            {
                "name": "Child, Company B",
                "is_company": False,
                "company_id": False,
                "parent_id": cls.partner_company_b.id,
            }
        )
        cls.company_b.partner_id = cls.partner_company_b
        # cls.partner_company_b = cls.company_b.parent_id.partner_id
        cls.user_company_a = cls.env["res.users"].create(
            {
                "name": "User A",
                "login": "usera",
                "company_type": "person",
                "email": "usera@yourcompany.com",
                "password": "usera_p4S$word",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, [cls.company_a.id])],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_partner_manager").id,
                            cls.env.ref("account.group_account_manager").id,
                            cls.env.ref("account.group_account_readonly").id,
                        ],
                    )
                ],
            }
        )
        cls.user_company_b = cls.env["res.users"].create(
            {
                "name": "User B",
                "login": "userb",
                "company_type": "person",
                "email": "userb@yourcompany.com",
                "password": "userb_p4S$word",
                "company_id": cls.company_b.id,
                "company_ids": [(6, 0, [cls.company_b.id])],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_partner_manager").id,
                            cls.env.ref("account.group_account_manager").id,
                        ],
                    )
                ],
            }
        )
        cls.sequence_sale_journal_company_a = cls.env["ir.sequence"].create(
            {
                "name": "Account Sales Journal Company A",
                "padding": 3,
                "prefix": "SAJ-A/%(year)s/",
                "company_id": cls.company_a.id,
            }
        )
        cls.sequence_misc_journaal_company_a = cls.env["ir.sequence"].create(
            {
                "name": "Miscellaneous Journal Company A",
                "padding": 3,
                "prefix": "MISC-A/%(year)s/",
                "company_id": cls.company_a.id,
            }
        )
        cls.sequence_purchase_journal_company_a = cls.env["ir.sequence"].create(
            {
                "name": "Account Expenses Journal Company A",
                "padding": 3,
                "prefix": "EXJ-A/%(year)s/",
                "company_id": cls.company_a.id,
            }
        )
        cls.sequence_sale_journal_company_b = cls.env["ir.sequence"].create(
            {
                "name": "Account Sales Journal Company B",
                "padding": 3,
                "prefix": "SAJ-B/%(year)s/",
                "company_id": cls.company_b.id,
            }
        )
        cls.sequence_misc_journal_company_b = cls.env["ir.sequence"].create(
            {
                "name": "Miscellaneous Journal Company B",
                "padding": 3,
                "prefix": "MISC-B/%(year)s/",
                "company_id": cls.company_b.id,
            }
        )
        cls.sequence_purchase_journal_company_b = cls.env["ir.sequence"].create(
            {
                "name": "Account Expenses Journal Company B",
                "padding": 3,
                "prefix": "EXJ-B/%(year)s/",
                "company_id": cls.company_b.id,
            }
        )

        cls.sequence_misc_journal_company_a = cls.env["ir.sequence"].create(
            {
                "name": "Miscellaneous Journal Company A",
                "padding": 3,
                "prefix": "MISC-A/%(year)s/",
                "company_id": cls.company_a.id,
            }
        )
        cls.sequence_purchase_journal_company_a = cls.env["ir.sequence"].create(
            {
                "name": "Account Expenses Journal Company A",
                "padding": 3,
                "prefix": "EXJ-A/%(year)s/",
                "company_id": cls.company_a.id,
            }
        )
        cls.sequence_sale_journal_company_b = cls.env["ir.sequence"].create(
            {
                "name": "Account Sales Journal Company B",
                "padding": 3,
                "prefix": "SAJ-B/%(year)s/",
                "company_id": cls.company_b.id,
            }
        )
        cls.sequence_misc_journal_company_b = cls.env["ir.sequence"].create(
            {
                "name": "Miscellaneous Journal Company B",
                "padding": 3,
                "prefix": "MISC-B/%(year)s/",
                "company_id": cls.company_b.id,
            }
        )
        cls.sequence_purchase_journal_company_b = cls.env["ir.sequence"].create(
            {
                "name": "Account Expenses Journal Company B",
                "padding": 3,
                "prefix": "EXJ-B/%(year)s/",
                "company_id": cls.company_b.id,
            }
        )

        cls.a_sale_company_a = cls.account_obj.create(
            {
                "code": "X2001.A",
                "name": "Product Sales - (company A)",
                "account_type": "income_other",
                "company_id": cls.company_a.id,
            }
        )
        cls.a_expense_company_a = cls.account_obj.create(
            {
                "code": "X2110.A",
                "name": "Expenses - (company A)",
                "account_type": "income_other",
                "company_id": cls.company_a.id,
            }
        )
        cls.a_bank_company_a = cls.account_obj.create(
            {
                "code": "512001.A",
                "name": "Bank - (company A)",
                "account_type": "asset_cash",
                "company_id": cls.company_a.id,
            }
        )
        cls.a_recv_company_b = cls.account_obj.create(
            {
                "code": "X11002.B",
                "name": "Debtors - (company B)",
                "account_type": "asset_receivable",
                "reconcile": "True",
                "company_id": cls.company_b.id,
            }
        )
        cls.a_pay_company_b = cls.account_obj.create(
            {
                "code": "X1111.B",
                "name": "Creditors - (company B)",
                "account_type": "liability_payable",
                "reconcile": "True",
                "company_id": cls.company_b.id,
            }
        )
        cls.a_sale_company_b = cls.account_obj.create(
            {
                "code": "X2001.B",
                "name": "Product Sales - (company B)",
                "account_type": "income_other",
                "company_id": cls.company_b.id,
            }
        )
        cls.a_expense_company_b = cls.account_obj.create(
            {
                "code": "X2110.B",
                "name": "Expenses - (company B)",
                "account_type": "expense",
                "company_id": cls.company_b.id,
            }
        )
        cls.a_bank_company_b = cls.account_obj.create(
            {
                "code": "512001.B",
                "name": "Bank - (company B)",
                "account_type": "asset_cash",
                "company_id": cls.company_b.id,
            }
        )

        cls.sales_journal_company_a = cls.env["account.journal"].create(
            {
                "name": "Sales Journal - (Company A)",
                "code": "SAJ-A",
                "type": "sale",
                "secure_sequence_id": cls.sequence_sale_journal_company_a.id,
                "default_account_id": cls.a_sale_company_a.id,
                "company_id": cls.company_a.id,
            }
        )

        cls.bank_journal_company_a = cls.env["account.journal"].create(
            {
                "name": "Bank Journal - (Company A)",
                "code": "BNK-A",
                "type": "bank",
                "default_account_id": cls.a_sale_company_a.id,
                "company_id": cls.company_a.id,
            }
        )
        cls.misc_journal_company_a = cls.env["account.journal"].create(
            {
                "name": "Miscellaneous Operations - (Company A)",
                "code": "MISC-A",
                "type": "general",
                "secure_sequence_id": cls.sequence_misc_journal_company_a.id,
                "company_id": cls.company_a.id,
            }
        )
        cls.purchases_journal_company_b = cls.env["account.journal"].create(
            {
                "name": "Purchases Journal - (Company B)",
                "code": "EXJ-B",
                "type": "purchase",
                "secure_sequence_id": cls.sequence_purchase_journal_company_b.id,
                "default_account_id": cls.a_expense_company_b.id,
                "company_id": cls.company_b.id,
            }
        )
        cls.bank_journal_company_b = cls.env["account.journal"].create(
            {
                "name": "Bank Journal - (Company B)",
                "code": "BNK-B",
                "type": "bank",
                "default_account_id": cls.a_sale_company_b.id,
                "company_id": cls.company_b.id,
            }
        )
        cls.misc_journal_company_b = cls.env["account.journal"].create(
            {
                "name": "Miscellaneous Operations - (Company B)",
                "code": "MISC-B",
                "type": "general",
                "secure_sequence_id": cls.sequence_misc_journal_company_b.id,
                "company_id": cls.company_b.id,
            }
        )
        cls.product_consultant_multi_company = cls.env.ref(
            "account_invoice_inter_company.product_consultant_multi_company"
        )
        # if product_multi_company is installed
        if "company_ids" in cls.env["product.template"]._fields:
            # We have to do that because the default method added a company
            cls.product_consultant_multi_company.company_ids = False

        cls.env["ir.sequence"].create(
            {
                "name": "Account Sales Journal Company A",
                "prefix": "SAJ-A/%(year)s/",
                "company_id": cls.company_a.id,
            }
        )
        cls.pcg_X58 = cls.env["account.account.template"].create(
            {
                "name": "Internal Transfers",
                "code": "X58",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )

        cls.a_recv_company_a = cls.account_obj.create(
            {
                "code": "X11002.A",
                "name": "Debtors - (company A)",
                "account_type": "asset_receivable",
                "reconcile": "True",
                "company_id": cls.company_a.id,
            }
        )
        cls.a_pay_company_a = cls.account_obj.create(
            {
                "code": "X1111.A",
                "name": "Creditors - (company A)",
                "account_type": "liability_payable",
                "reconcile": "True",
                "company_id": cls.company_a.id,
            }
        )

        cls.partner_company_a.property_account_receivable_id = cls.a_recv_company_a.id
        cls.partner_company_a.property_account_payable_id = cls.a_pay_company_a.id

        cls.partner_company_b.property_account_receivable_id = cls.a_recv_company_b.id
        cls.partner_company_b.property_account_payable_id = cls.a_pay_company_b.id

        cls.invoice_company_a = Form(
            cls.account_move_obj.with_user(cls.user_company_a.id).with_context(
                default_move_type="out_invoice",
            )
        )
        cls.invoice_company_a.partner_id = cls.partner_company_b
        cls.invoice_company_a.journal_id = cls.sales_journal_company_a
        cls.invoice_company_a.currency_id = cls.env.ref("base.EUR")

        with cls.invoice_company_a.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.product_consultant_multi_company
            line_form.quantity = 1
            line_form.product_uom_id = cls.env.ref("uom.product_uom_hour")
            line_form.account_id = cls.a_sale_company_a
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        cls.invoice_company_a = cls.invoice_company_a.save()
        cls.invoice_line_a = cls.invoice_company_a.invoice_line_ids[0]

        cls.company_a.invoice_auto_validation = True

        cls.product_a = cls.invoice_line_a.product_id
        cls.product_a.with_user(
            cls.user_company_b.id
        ).property_account_expense_id = cls.a_expense_company_b.id


class TestAccountInvoiceInterCompany(TestAccountInvoiceInterCompanyBase):
    def test01_user(self):
        # Check user of company B (company of destination)
        # with which we check the intercompany product
        self.assertNotEqual(self.user_company_b.id, 1)
        orig_invoice = self.invoice_company_a
        dest_company = orig_invoice._find_company_from_invoice_partner()
        self.assertEqual(self.user_company_b.company_id, dest_company)
        self.assertIn(
            self.user_company_b.id,
            self.env.ref("account.group_account_invoice").users.ids,
        )

    def test02_product(self):
        # Check product is intercompany
        for line in self.invoice_company_a.invoice_line_ids:
            self.assertFalse(line.product_id.company_id)

    def test03_confirm_invoice_and_cancel(self):
        # ensure the catalog is shared
        self.env.ref("product.product_comp_rule").write({"active": False})
        # Make sure there are no taxes in target company for the used product
        self.product_a.with_user(self.user_company_b.id).supplier_taxes_id = False
        # Confirm the invoice of company A
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        # Check destination invoice created in company B
        invoices = self.account_move_obj.with_user(self.user_company_b.id).search(
            [("auto_invoice_id", "=", self.invoice_company_a.id)]
        )
        self.assertNotEqual(invoices, False)
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].state, "posted")
        self.assertEqual(
            invoices[0].partner_id,
            self.invoice_company_a.company_id.partner_id,
        )
        self.assertEqual(
            invoices[0].company_id.partner_id,
            self.invoice_company_a.partner_id,
        )
        self.assertEqual(
            len(invoices[0].invoice_line_ids),
            len(self.invoice_company_a.invoice_line_ids),
        )
        invoice_line = invoices[0].invoice_line_ids[0]
        self.assertEqual(
            invoice_line.product_id,
            self.invoice_company_a.invoice_line_ids[0].product_id,
        )
        # Cancel the invoice of company A
        invoice_origin = ("%s - Canceled Invoice: %s") % (
            self.invoice_company_a.company_id.name,
            self.invoice_company_a.name,
        )
        self.invoice_company_a.with_user(self.user_company_a.id).button_cancel()
        # Check invoices after to cancel invoice of company A
        self.assertEqual(self.invoice_company_a.state, "cancel")
        self.assertEqual(invoices[0].state, "cancel")
        self.assertEqual(invoices[0].invoice_origin, invoice_origin)
        # Check if keep the invoice number
        invoice_number = self.invoice_company_a.name
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        self.assertEqual(self.invoice_company_a.name, invoice_number)
        # When the destination invoice is posted we can't modify the origin either
        with self.assertRaises(UserError):
            self.invoice_company_a.with_context(breakpoint=True).button_draft()
        # Check that we can't modify the destination invoice
        dest_invoice = self.account_move_obj.search(
            [("auto_invoice_id", "=", self.invoice_company_a.id)]
        )
        dest_invoice.button_draft()
        with self.assertRaises(UserError):
            move_form = Form(dest_invoice)
            with move_form.invoice_line_ids.edit(0) as line_form:
                line_form.price_unit = 33.3
            move_form.save()

    def test_confirm_invoice_with_child_partner(self):
        # ensure the catalog is shared
        self.env.ref("product.product_comp_rule").write({"active": False})
        # When a contact of the company is defined as partner,
        # it also must trigger the intercompany workflow
        self.invoice_company_a.write({"partner_id": self.child_partner_company_b.id})
        # Confirm the invoice of company A
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        # Check destination invoice created in company B
        invoices = self.account_move_obj.with_user(self.user_company_b.id).search(
            [("auto_invoice_id", "=", self.invoice_company_a.id)]
        )
        self.assertEqual(len(invoices), 1)

    def test_confirm_invoice_with_product_and_shared_catalog(self):
        """With no security rule, child company have access to any product.
        Then child invoice can share the same product
        """
        # ensure the catalog is shared even if product is in other company
        self.env.ref("product.product_comp_rule").write({"active": False})
        # Product is set to a specific company
        self.product_a.write({"company_id": self.company_a.id})
        invoices = self._confirm_invoice_with_product()
        self.assertNotEqual(
            invoices.invoice_line_ids[0].product_id, self.env["product.product"]
        )

    def test_confirm_invoice_with_native_product_rule_and_shared_product(self):
        """With native security rule, products with access in both companies
        must be present in parent and child invoices.
        """
        # ensure the catalog is shared even if product is in other company
        self.env.ref("product.product_comp_rule").write({"active": True})
        # Product is set to a specific company
        self.product_a.write({"company_id": False})
        # If product_multi_company is installed
        if "company_ids" in dir(self.product_a):
            self.product_a.write({"company_ids": [(5, 0, 0)]})
        invoices = self._confirm_invoice_with_product()
        self.assertEqual(invoices.invoice_line_ids[0].product_id, self.product_a)

    def test_confirm_invoice_with_native_product_rule_and_unshared_product(self):
        """With native security rule, products with no access in both companies
        must prevent child invoice creation.
        """
        # ensure the catalog is shared even if product is in other company
        self.env.ref("product.product_comp_rule").write({"active": True})
        # Product is set to a specific company
        self.product_a.write({"company_id": self.company_a.id})
        # If product_multi_company is installed
        if "company_ids" in dir(self.product_a):
            self.product_a.write({"company_ids": [(6, 0, [self.company_a.id])]})
        with self.assertRaises(UserError):
            self._confirm_invoice_with_product()

    def _confirm_invoice_with_product(self):
        # Confirm the invoice of company A
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        # Check destination invoice created in company B
        invoices = self.account_move_obj.with_user(self.user_company_b.id).search(
            [("auto_invoice_id", "=", self.invoice_company_a.id)]
        )
        self.assertEqual(len(invoices), 1)
        return invoices

    def test_confirm_invoice_intercompany_disabled(self):
        # ensure the catalog is shared
        self.env.ref("product.product_comp_rule").write({"active": False})
        # Disable the configuration in company A
        self.company_a.intercompany_invoicing = False
        # Confirm the invoice of company A
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        # Check that no destination invoice has been created in company B
        invoices = self.account_move_obj.with_user(self.user_company_b.id).search(
            [("auto_invoice_id", "=", self.invoice_company_a.id)]
        )
        self.assertFalse(invoices)
