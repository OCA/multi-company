# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tests.common import SavepointCase
from odoo.tools import convert_file


class TestConsolidatedInvoice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestConsolidatedInvoice, cls).setUpClass()
        module = "account_invoice_consolidated"
        convert_file(
            cls.cr,
            module,
            get_resource_path(module, "tests", "test_consolidated_invoices_data.xml"),
            None,
            "init",
            False,
            "test",
            None,
        )
        cls.product_id = cls.env.ref("product.product_product_1")
        cls.company_a = cls.env.ref("account_invoice_consolidated.company_a")
        cls.company_b = cls.env.ref("account_invoice_consolidated.company_b")
        cls.account_b = cls.env.ref("account_invoice_consolidated.a_sale_company_b")
        cls.account_a = cls.env.ref("account_invoice_consolidated.a_sale_company_a")

        cls.partner_user = cls.env.ref("account_invoice_consolidated.partner_user_a")
        cls.consolidated_inv_obj = cls.env["account.invoice.consolidated"]
        cls.account_obj = cls.env["account.account"]
        cls.invoice_obj_a = cls.env.ref(
            "account_invoice_consolidated.customer_invoice_company_a"
        )
        cls.invoice_obj_a.partner_id = cls.partner_user
        cls.invoice_obj_a.invoice_date = date.today() + relativedelta(months=-3)
        cls.invoice_obj_a.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_id.id,
                            "name": cls.product_id.name,
                            "account_id": cls.account_a.id,
                            "price_unit": 450.0,
                            "company_id": cls.company_a.id,
                        },
                    )
                ]
            }
        )

        cls.invoice_obj_a.sudo().action_post()

        cls.invoice_obj_b = cls.env.ref(
            "account_invoice_consolidated.customer_invoice_company_b"
        )
        cls.invoice_obj_b.partner_id = cls.partner_user
        cls.invoice_obj_b.invoice_date = date.today() + relativedelta(months=-3)
        cls.invoice_obj_b.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_id.id,
                            "name": cls.product_id.name,
                            "account_id": cls.account_b.id,
                            "price_unit": 450.0,
                            "company_id": cls.company_b.id,
                        },
                    )
                ]
            }
        )

        cls.invoice_obj_b.sudo().action_post()

        cls.company_a = cls.env.ref("account_invoice_consolidated.company_a")
        cls.company_b = cls.env.ref("account_invoice_consolidated.company_b")

        cls.env.user.company_id = cls.company_a

        cls.company_a.due_fromto_payment_journal_id = cls.env.ref(
            "account_invoice_consolidated.sales_journal_company_a"
        )
        cls.company_b.due_fromto_payment_journal_id = cls.env.ref(
            "account_invoice_consolidated.bank_journal_company_b"
        )

        cls.company_b.due_fromto_payment_journal_id.payment_debit_account_id = (
            cls.env.ref("account_invoice_consolidated.a_expense_company_b")
        )

        cls.company_a.due_from_account_id = cls.env.ref(
            "account_invoice_consolidated.a_pay_company_a"
        )
        cls.company_a.due_to_account_id = cls.env.ref(
            "account_invoice_consolidated.a_recv_company_a"
        )
        cls.company_b.due_from_account_id = cls.env.ref(
            "account_invoice_consolidated.a_recv_company_b"
        )
        cls.company_b.due_to_account_id = cls.env.ref(
            "account_invoice_consolidated.a_pay_company_b"
        )

        cls.company_a_journal = cls.env.ref(
            "account_invoice_consolidated.bank_journal_company_a"
        )

        cls.company_b_journal = cls.env.ref(
            "account_invoice_consolidated.bank_journal_company_b"
        )

        cls.chart = cls.env["account.chart.template"].search([], limit=1)
        if not cls.chart:
            raise ValidationError(
                # translation to avoid pylint warnings
                _("No Chart of Account Template has been defined !")
            )

    def test_consolidated_invoice(self):
        inv = self.consolidated_inv_obj.create(
            {
                "company_id": self.company_a.id,
                "date_from": datetime.today() + relativedelta(months=-6),
                "date_to": datetime.today(),
                "partner_id": self.partner_user.id,
            }
        )

        inv.sudo().get_invoices()
        self.assertIn(self.invoice_obj_a.id, inv.invoice_ids.ids)
        self.assertIn(self.invoice_obj_b.id, inv.invoice_ids.ids)

        # Calculate the total price
        inv.sudo().get_invoice_price()
        self.assertEqual(
            (self.invoice_obj_a.amount_residual + self.invoice_obj_b.amount_residual),
            inv.amount_total,
        )

        # Confirm the invoice and verify both invoices have been paid
        inv.sudo().action_confirm_invoice()
        self.assertEqual(self.invoice_obj_a.payment_state, "paid")
        self.assertEqual(self.invoice_obj_b.payment_state, "paid")

        with self.assertRaises(ValidationError):
            inv.write({"name": "Test"})
            inv2 = self.consolidated_inv_obj.create(
                {
                    "company_id": self.company_a.id,
                    "date_from": datetime.today() + relativedelta(months=-6),
                    "date_to": datetime.today(),
                    "partner_id": self.partner_user.id,
                }
            )
            inv2.write({"name": "Test"})

        self.partner_user.view_consolidated_invoice()

        with self.assertRaises(ValidationError):
            vals = {
                "date_to": datetime.today() + relativedelta(months=-6),
                "date_from": datetime.today(),
            }
            inv.update(vals)

        with self.assertRaises(ValidationError):
            self.consolidated_inv_obj.create(
                {
                    "company_id": self.company_a.id,
                    "date_from": datetime.today() + relativedelta(months=-6),
                    "date_to": datetime.today(),
                    "partner_id": self.partner_user.id,
                }
            )

        with self.assertRaises(ValidationError):
            inv.sudo().unlink()
        inv.sudo().write({"state": "draft"})
        inv.sudo().unlink()

    def test_consolidated_invoice_01(self):
        inv = self.consolidated_inv_obj.create(
            {
                "company_id": self.company_a.id,
                "date_from": datetime.today() + relativedelta(months=-6),
                "date_to": datetime.today(),
                "partner_id": self.partner_user.id,
            }
        )

        inv.sudo().get_invoices()

        # Calculate the total price
        inv.sudo().get_invoice_price()

        with self.assertRaises(ValidationError):
            inv.update({"invoice_ids": []})
            # Confirm the invoice and verify both invoices have been paid
            inv.sudo().action_confirm_invoice()

    def test_consolidated_tax(self):
        inv = self.consolidated_inv_obj.create(
            {
                "company_id": self.company_a.id,
                "date_from": datetime.today() + relativedelta(months=-6),
                "date_to": datetime.today(),
                "partner_id": self.partner_user.id,
            }
        )
        tax_price_include = self.env["account.tax"].create(
            {
                "name": "10% incl",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 10,
                "company_id": self.company_a.id,
            }
        )
        inv.get_tax(tax_price_include)
