# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tools import convert_file


class TestAccountPayment(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountPayment, cls).setUpClass()
        module = "account_payment_other_company"
        convert_file(
            cls.cr, module,
            get_resource_path(module, "tests",
                              "test_account_payment_data.xml"),
            None, 'init', False, 'test', cls.registry._assertion_report,
        )
        cls.account_obj = cls.env['account.account']
        cls.invoice_obj = cls.env.ref(
            'account_payment_other_company.customer_invoice_company_a')
        cls.vendor_bill_obj = cls.env.ref(
            'account_payment_other_company.vendor_bill_company_a')
        cls.company_a = cls.env.ref(
            'account_payment_other_company.company_a')
        cls.company_b = cls.env.ref(
            'account_payment_other_company.company_b')
        cls.account_payment_obj = cls.env['account.payment']
        cls.journal_1 = cls.env['account.journal']
        cls.journal_2 = cls.env['account.journal']
        cls.account_dt1 = cls.env['account.account']
        cls.account_dt2 = cls.env['account.account']
        cls.account_df1 = cls.env['account.account']
        cls.account_d21 = cls.env['account.account']

        cls.company_a.due_fromto_payment_journal_id = cls.env.ref(
            'account_payment_other_company.sales_journal_company_a'
        )
        cls.company_a.due_fromto_payment_journal_id.update_posted = True
        cls.company_b.due_fromto_payment_journal_id = cls.env.ref(
            'account_payment_other_company.bank_journal_company_b'
        )

        cls.company_b.due_fromto_payment_journal_id.\
            default_debit_account_id = cls.env.ref(
                'account_payment_other_company.a_expense_company_b'
            )

        cls.company_a.due_from_account_id = cls.env.ref(
            'account_payment_other_company.a_pay_company_a'
        )
        cls.company_a.due_to_account_id = cls.env.ref(
            'account_payment_other_company.a_recv_company_a'
        )
        cls.company_b.due_from_account_id = cls.env.ref(
            'account_payment_other_company.a_recv_company_b'
        )
        cls.company_b.due_to_account_id = cls.env.ref(
            'account_payment_other_company.a_pay_company_b'
        )

        cls.company_a_journal = cls.env.\
            ref('account_payment_other_company.bank_journal_company_a')

        cls.company_b_journal = cls.env.\
            ref('account_payment_other_company.bank_journal_company_b')
        cls.company_b_journal.update_posted = True

        cls.chart = cls.env['account.chart.template'].search([], limit=1)

        if not cls.chart:
            raise ValidationError(
                # translation to avoid pylint warnings
                _("No Chart of Account Template has been defined !"))

    def test_customer_payment_same_co(self):
        self.invoice_obj.action_invoice_open()
        vals = {
            'amount': self.invoice_obj.amount_total,
            'journal_id': self.company_a_journal.id,
            'company_id': self.company_a.id,
            'payment_type': 'outbound',
            'currency_id': self.invoice_obj.currency_id.id,
            'payment_date': self.invoice_obj.date_invoice,
            'communication': 'findme',
            # 'other_journal_id': cls.company_b_journal.id,
            'payment_method_id': 1,
            'partner_type': 'supplier',
            'partner_id': self.env.ref('base.res_partner_1').id,
            'show_other_journal': False
        }
        payment = self.account_payment_obj.create(vals)
        payment.invoice_ids = [self.invoice_obj.id]
        payment.action_validate_invoice_payment()

    def test_vendor_payment_other_co(self):
        self.invoice_obj.action_invoice_open()
        vals = {
            'amount': self.invoice_obj.amount_total,
            'journal_id': self.company_a.due_fromto_payment_journal_id.id,
            'company_id': self.company_a.id,
            'payment_type': 'outbound',
            'currency_id': self.invoice_obj.currency_id.id,
            'payment_date': self.invoice_obj.date_invoice,
            'communication': 'findme',
            'other_journal_id': self.company_b_journal.id,
            'payment_method_id': 1,
            'partner_type': 'supplier',
            'partner_id': self.env.ref('base.res_partner_1').id,
            'show_other_journal': False
        }
        payment = self.account_payment_obj.create(vals)
        payment.invoice_ids = [self.invoice_obj.id]
        payment.action_validate_invoice_payment()
        ref = _("%s from %s" % (payment.name, payment.company_id.name))
        move = self.env['account.move'].sudo().\
            search([('ref', '=', ref)])

        # Check Credit/Debit
        self.assertEquals(move.line_ids[0].credit,
                          self.invoice_obj.amount_total)
        self.assertEquals(move.line_ids[0].debit,
                          0.0)
        self.assertEquals(move.line_ids[1].credit,
                          0.0)
        self.assertEquals(move.line_ids[1].debit,
                          self.invoice_obj.amount_total)

        # Check Accounts
        self.assertEquals(move.line_ids[0].account_id,
                          payment.other_journal_id.default_credit_account_id
                          )
        self.assertEquals(move.line_ids[1].account_id,
                          payment.other_journal_id.company_id.
                          due_to_account_id)

        # Check Partners
        self.assertEquals(move.line_ids[0].partner_id, payment.partner_id)
        self.assertEquals(move.line_ids[1].partner_id,
                          payment.company_id.partner_id)
