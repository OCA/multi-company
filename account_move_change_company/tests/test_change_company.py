# Copyright 2022 CreuBlanca
# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("-at_install", "post_install")
class TestChangeCompany(AccountTestInvoicingCommon):
    def test_change_in_invoice(self):
        invoice = self.init_invoice(
            "in_invoice", products=self.product_a + self.product_b
        )
        # self.assertEqual(invoice.company_id)
        company = self.company_data_2["company"]
        self.assertNotEqual(invoice.company_id, company)
        invoice = (
            self.env[invoice._name]
            .with_context(allowed_company_ids=self.env.companies.ids + company.ids)
            .browse(invoice.ids)
        )
        with Form(invoice) as f:
            f.company_id = company
        self.assertTrue(invoice.line_ids)
        self.assertEqual(invoice.journal_id.company_id, company)
        for line in invoice.line_ids:
            self.assertEqual(line.company_id, company)
            self.assertEqual(line.account_id.company_id, company)
            for tax in line.tax_ids:
                self.assertEqual(tax.company_id, company)

    def test_change_out_invoice(self):
        invoice = self.init_invoice(
            "out_invoice", products=self.product_a + self.product_b
        )
        # self.assertEqual(invoice.company_id)
        company = self.company_data_2["company"]
        self.assertNotEqual(invoice.company_id, company)
        invoice = (
            self.env[invoice._name]
            .with_context(allowed_company_ids=self.env.companies.ids + company.ids)
            .browse(invoice.ids)
        )
        with Form(invoice) as f:
            f.company_id = company
        self.assertTrue(invoice.line_ids)
        self.assertEqual(invoice.journal_id.company_id, company)
        for line in invoice.line_ids:
            self.assertEqual(line.company_id, company)
            self.assertEqual(line.account_id.company_id, company)
            for tax in line.tax_ids:
                self.assertEqual(tax.company_id, company)

    def test_change_extra_fields(self):
        invoice = self.init_invoice(
            "out_invoice", products=self.product_a + self.product_b
        )
        # self.assertEqual(invoice.company_id)
        company = self.company_data_2["company"]
        fp = (
            self.env["account.fiscal.position"]
            .with_company(company.id)
            .create(
                {
                    "name": "Test",
                    "sequence": 1,
                }
            )
        )
        term = (
            self.env["account.payment.term"]
            .with_company(company.id)
            .create({"name": "Test", "company_id": company.id})
        )
        invoice.invoice_payment_term_id = False
        invoice.partner_id.with_company(company.id).write(
            {"property_account_position_id": fp.id, "property_payment_term_id": term.id}
        )
        self.assertNotEqual(invoice.company_id, company)
        invoice = (
            self.env[invoice._name]
            .with_context(allowed_company_ids=self.env.companies.ids + company.ids)
            .browse(invoice.ids)
        )
        with Form(invoice) as f:
            f.company_id = company
        self.assertTrue(invoice.line_ids)
        self.assertEqual(invoice.journal_id.company_id, company)
        self.assertEqual(invoice.fiscal_position_id, fp)
        self.assertEqual(invoice.invoice_payment_term_id, term)
        for line in invoice.line_ids:
            self.assertEqual(line.company_id, company)
            self.assertEqual(line.account_id.company_id, company)
            for tax in line.tax_ids:
                self.assertEqual(tax.company_id, company)

    def test_change_entry(self):
        tax_repartition_line = self.company_data[
            "default_tax_sale"
        ].refund_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        company = self.company_data_2["company"]
        account_entry = (
            self.env["account.move"]
            .with_context(
                allowed_company_ids=self.env.companies.ids
                + company.ids
                + self.company_data["company"].ids
            )
            .create(
                {
                    "move_type": "entry",
                    "date": "2016-01-01",
                    "line_ids": [
                        (
                            0,
                            None,
                            {
                                "name": "revenue line 1",
                                "account_id": self.company_data[
                                    "default_account_revenue"
                                ].id,
                                "debit": 500.0,
                                "credit": 0.0,
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "name": "revenue line 2",
                                "account_id": self.company_data[
                                    "default_account_revenue"
                                ].id,
                                "debit": 1000.0,
                                "credit": 0.0,
                                "tax_ids": [
                                    (6, 0, self.company_data["default_tax_sale"].ids)
                                ],
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "name": "tax line",
                                "account_id": self.company_data[
                                    "default_account_tax_sale"
                                ].id,
                                "debit": 150.0,
                                "credit": 0.0,
                                "tax_repartition_line_id": tax_repartition_line.id,
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "name": "counterpart line",
                                "account_id": self.company_data[
                                    "default_account_expense"
                                ].id,
                                "debit": 0.0,
                                "credit": 1650.0,
                            },
                        ),
                    ],
                }
            )
        )
        self.assertTrue(account_entry.line_ids)
        with Form(account_entry) as f:
            f.company_id = company
        self.assertFalse(account_entry.line_ids)
        self.assertEqual(account_entry.journal_id.company_id, company)
