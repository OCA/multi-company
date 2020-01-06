# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tools import convert_file
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class TestConsolidatedInvoice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestConsolidatedInvoice, cls).setUpClass()
        module = "account_invoice_consolidated"
        convert_file(
            cls.cr, module,
            get_resource_path(module, "tests",
                              "test_consolidated_invoices_data.xml"),
            None, 'init', False, 'test', cls.registry._assertion_report,
        )

        cls.partner_user = cls.env.\
            ref('account_invoice_consolidated.partner_user_a')
        cls.consolidated_inv_obj = cls.env['account.invoice.consolidated']
        cls.account_obj = cls.env['account.account']
        cls.invoice_obj_a = cls.env.ref(
            'account_invoice_consolidated.customer_invoice_company_a')
        cls.invoice_obj_a.partner_id = cls.partner_user
        cls.invoice_obj_a.date_invoice = date.\
            today() + relativedelta(months=-3)
        cls.invoice_obj_a.sudo().action_invoice_open()

        cls.invoice_obj_b = cls.env.ref(
            'account_invoice_consolidated.customer_invoice_company_b')
        cls.invoice_obj_b.partner_id = cls.partner_user
        cls.invoice_obj_b.date_invoice = date.\
            today() + relativedelta(months=-3)
        cls.invoice_obj_b.sudo().action_invoice_open()

        cls.company_a = cls.env.ref(
            'account_invoice_consolidated.company_a')
        cls.company_b = cls.env.ref(
            'account_invoice_consolidated.company_b')

        cls.env.user.company_id = cls.company_a

        cls.journal_1 = cls.env['account.journal']
        cls.journal_2 = cls.env['account.journal']
        cls.account_dt1 = cls.env['account.account']
        cls.account_dt2 = cls.env['account.account']
        cls.account_df1 = cls.env['account.account']
        cls.account_d21 = cls.env['account.account']

        cls.company_a.due_fromto_payment_journal_id = cls.env.ref(
            'account_invoice_consolidated.sales_journal_company_a'
        )
        cls.company_b.due_fromto_payment_journal_id = cls.env.ref(
            'account_invoice_consolidated.bank_journal_company_b'
        )

        cls.company_b.due_fromto_payment_journal_id.\
            default_debit_account_id = cls.env.ref(
                'account_invoice_consolidated.a_expense_company_b'
            )

        cls.company_a.due_from_account_id = cls.env.ref(
            'account_invoice_consolidated.a_pay_company_a'
        )
        cls.company_a.due_to_account_id = cls.env.ref(
            'account_invoice_consolidated.a_recv_company_a'
        )
        cls.company_b.due_from_account_id = cls.env.ref(
            'account_invoice_consolidated.a_recv_company_b'
        )
        cls.company_b.due_to_account_id = cls.env.ref(
            'account_invoice_consolidated.a_pay_company_b'
        )

        cls.company_a_journal = cls.env.\
            ref('account_invoice_consolidated.bank_journal_company_a')

        cls.company_b_journal = cls.env.\
            ref('account_invoice_consolidated.bank_journal_company_b')

        cls.chart = cls.env['account.chart.template'].search([], limit=1)
        if not cls.chart:
            raise ValidationError(
                # translation to avoid pylint warnings
                _("No Chart of Account Template has been defined !"))

    def test_consolidated_invoice(self):
        inv = self.consolidated_inv_obj.create({
            'company_id': self.company_a.id,
            'date_from': datetime.today() + relativedelta(months=-6),
            'date_to': datetime.today(),
            'partner_id': self.partner_user.id
        })
        # Get invoices
        inv.sudo().get_invoices()
        self.assertIn(self.invoice_obj_a.id, inv.invoice_ids.ids)
        self.assertIn(self.invoice_obj_b.id, inv.invoice_ids.ids)

        # Calculate the total price
        inv.sudo().get_invoice_price()
        self.assertEqual((self.invoice_obj_a.residual +
                          self.invoice_obj_b.residual), inv.amount_total)

        # Confirm the invoice and verify both invoices have been paid
        inv.sudo().action_confirm_invoice()
        self.assertEqual(self.invoice_obj_a.state, 'paid')
        self.assertEqual(self.invoice_obj_b.state, 'paid')
