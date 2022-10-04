# Copyright 2022 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)


class TestAccountPaymentOrderInterCompany(TestAccountInvoiceInterCompanyBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Payment mode in company B
        cls.payment_mode_company_b = cls.env["account.payment.mode"].create(
            {
                "name": "Test Credit Transfer to Suppliers",
                "company_id": cls.company_b.id,
                "bank_account_link": "variable",
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_out"
                ).id,
            }
        )
        # Payment mode in company A
        cls.payment_mode_company_a = cls.env["account.payment.mode"].create(
            {
                "name": "Test Direct Debit of customers",
                "company_id": cls.company_a.id,
                "bank_account_link": "variable",
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
            }
        )
        # Supplier Invoice in Company B
        cls.invoice_company_b = Form(
            cls.account_move_obj.with_company(cls.company_b.id).with_context(
                default_move_type="in_invoice",
            )
        )
        cls.invoice_company_b.partner_id = cls.partner_company_a
        cls.invoice_company_b.invoice_date = cls.invoice_company_b.date
        cls.invoice_company_b.journal_id = cls.purchases_journal_company_b
        cls.invoice_company_b.currency_id = cls.env.ref("base.EUR")

        with cls.invoice_company_b.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.product_consultant_multi_company
            line_form.quantity = 1
            line_form.product_uom_id = cls.env.ref("uom.product_uom_hour")
            line_form.account_id = cls.a_expense_company_b
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        cls.invoice_company_b = cls.invoice_company_b.save()
        cls.invoice_line_b = cls.invoice_company_b.invoice_line_ids[0]

        cls.company_b.invoice_auto_validation = True

        cls.product_b = cls.invoice_line_b.product_id
        cls.product_b.with_company(
            cls.company_a.id
        ).property_account_income_id = cls.a_sale_company_a.id

    def _create_intercompany_supplier_invoice(self):
        # Confirm the customer invoice in company A
        self.invoice_company_a.with_user(self.user_company_a.id).with_context(
            test_queue_job_no_delay=True
        ).action_post()
        # Search supplier invoice created in company B
        invoice_company_b = self.account_move_obj.with_user(
            self.user_company_b.id
        ).search(
            [
                ("auto_invoice_id", "=", self.invoice_company_a.id),
                ("company_id", "=", self.company_b.id),
            ],
            limit=1,
        )
        return invoice_company_b

    def _create_intercompany_customer_invoice(self):
        # Confirm the supplier invoice in company B
        self.invoice_company_b.with_user(self.user_company_b.id).with_context(
            test_queue_job_no_delay=True
        ).action_post()
        # Search customer invoice created in company A
        invoice_company_a = self.account_move_obj.with_user(
            self.user_company_a.id
        ).search(
            [
                ("auto_invoice_id", "=", self.invoice_company_b.id),
                ("company_id", "=", self.company_a.id),
            ],
            limit=1,
        )
        return invoice_company_a

    def _pay_invoice(self, invoice, journal, payment_mode, payment_type, company):
        # Update payment_mode in invoice
        invoice.write({"payment_mode_id": payment_mode.id})
        # Create payment order
        self.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({}).run()
        payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_type", "=", payment_type),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )
        # Update journal in payment order
        payment_order.write({"journal_id": journal.id})
        # Update communication in payment lines
        for payment_line in payment_order.payment_line_ids:
            payment_line.write({"communication": invoice.name})
        # Confirm payment order
        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

    def test_create_customer_invoice_and_pay_supplier_invoice(self):
        # Create intercompany supplier invoice in company B
        invoice_company_b = self._create_intercompany_supplier_invoice()
        # Pay supplier invoice in company B
        self._pay_invoice(
            invoice_company_b,
            self.bank_journal_company_b,
            self.payment_mode_company_b,
            "outbound",
            self.company_b,
        )
        # Check payment state of supplier invoice in company B
        self.assertEqual(invoice_company_b.payment_state, "paid")
        # Check payment state of customer invoice in company A
        self.assertEqual(self.invoice_company_a.payment_state, "paid")

    def test_create_customer_invoice_and_pay_customer_invoice(self):
        # Create intercompany supplier invoice in company B
        invoice_company_b = self._create_intercompany_supplier_invoice()
        # Pay customer invoice in company A
        self._pay_invoice(
            self.invoice_company_a,
            self.bank_journal_company_a,
            self.payment_mode_company_a,
            "inbound",
            self.company_a,
        )
        # Check payment state of customer invoice in company A
        self.assertEqual(self.invoice_company_a.payment_state, "paid")
        # Check payment state of supplier invoice in company B
        self.assertEqual(invoice_company_b.payment_state, "paid")

    def test_create_supplier_invoice_and_pay_supplier_invoice(self):
        # Create intercompany customer invoice in company A
        invoice_company_a = self._create_intercompany_customer_invoice()
        # Pay supplier invoice in company B
        self._pay_invoice(
            self.invoice_company_b,
            self.bank_journal_company_b,
            self.payment_mode_company_b,
            "outbound",
            self.company_b,
        )
        # Check payment state of supplier invoice in company B
        self.assertEqual(self.invoice_company_b.payment_state, "paid")
        # Check payment state of customer invoice in company A
        self.assertEqual(invoice_company_a.payment_state, "paid")

    def test_create_supplier_invoice_and_pay_customer_invoice(self):
        # Create intercompany customer invoice in company A
        invoice_company_a = self._create_intercompany_customer_invoice()
        # Pay customer invoice in company A
        self._pay_invoice(
            invoice_company_a,
            self.bank_journal_company_a,
            self.payment_mode_company_a,
            "inbound",
            self.company_a,
        )
        # Check payment state of customer invoice in company A
        self.assertEqual(invoice_company_a.payment_state, "paid")
        # Check payment state of supplier invoice in company B
        self.assertEqual(self.invoice_company_b.payment_state, "paid")
