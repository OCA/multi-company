# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tools import convert_file


class TestAccountInvoice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountInvoice, cls).setUpClass()
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

    def test_bidirectional_computed_methods(self):
        dist_vals = [{
            'amount': 225,
            'percent': 50,
            'company': self.company_b.id,
            'invoice_line_id': self.invoice_obj.invoice_line_ids[0].id
        }]
        self.env['account.invoice.line.distribution'].create(dist_vals)
        dist1 = self.invoice_obj.\
            invoice_line_ids[0].distribution_ids[0]
        dist2 = self.invoice_obj.\
            invoice_line_ids[0].distribution_ids[1]

        # Both Distributions are Equal
        dist1.write({'amount': 225.00, 'percent': 50.00})
        self.assertEquals(dist1.amount, dist2.amount)
        self.assertEquals(dist1.percent, dist2.percent)

        # Change Amount
        dist1.write({'amount': 180.00})
        dist1.onchange_amount_total()

        self.assertEquals(dist1.percent, 40.00)

        self.invoice_obj.invoice_line_ids[0].\
            _onchange_distribution_ids_amount()
        self.invoice_obj.invoice_line_ids[0].\
            _onchange_distribution_ids_percent()

        self.assertEquals(dist2.percent, 60.00)
        self.assertEquals(dist2.amount, 270.00)

        # Change Percent
        dist1.write({'percent': 15.00})
        dist1.onchange_percent_total()
        self.assertEquals(dist1.amount, 67.50)

        self.invoice_obj.invoice_line_ids[0].\
            _onchange_distribution_ids_amount()
        self.invoice_obj.invoice_line_ids[0].\
            _onchange_distribution_ids_percent()

        self.assertEquals(dist2.percent, 85.00)
        self.assertEquals(dist2.amount, 382.50)

    def test_bill_distribution_account_move(self):
        dist_vals = [{
            'amount': 225,
            'percent': 50,
            'company_id': self.company_b.id,
            'invoice_line_id': self.vendor_bill_obj.invoice_line_ids[0].id
        }]
        self.env['account.invoice.line.distribution'].create(dist_vals)
        self.vendor_bill_obj.invoice_line_ids[0].distribution_ids[0].write({
            'amount': 225,
            'percent': 50
        })
        self.vendor_bill_obj.action_invoice_open()

        # Get
        due_to_from_move_ids = self.env['account.move'].sudo().\
            search([('ref', 'like', self.vendor_bill_obj.number)])

        # |---------------------|-----------------|
        # | Account |  Partner  | Debit  | Credit |
        # |---------------------|-----------------|
        # | Due To  | Company B | 0.00   | 225.00 |
        # |---------------------|-----------------|
        # | VB Line | Company B | 225.00 |  0.00  |
        # |---------------------|-----------------|

        # |--------------------|-----------------|
        # |Account |  Partner  | Debit  | Credit |
        # |--------------------|-----------------|
        # |VB Line | Company A |  0.00  | 225.00 |
        # |--------------------|-----------------|
        # |Due From| Company A | 225.00 |  0.00  |
        # |--------------------|-----------------|

        self.assertEquals(due_to_from_move_ids[0].amount,
                          due_to_from_move_ids[1].amount)
        for move_id in due_to_from_move_ids:
            if move_id.company_id != self.vendor_bill_obj.company_id:
                for line_id in move_id.line_ids:
                    if line_id.debit == 0.00:
                        self.assertEquals(line_id.account_id.id,
                                          self.company_b.due_to_account_id.id)
                    else:
                        self.assertEquals(line_id.account_id.code,
                                          self.vendor_bill_obj.
                                          invoice_line_ids[0].account_id.code)
            else:
                for line_id in move_id.line_ids:
                    if line_id.debit == 0.00:
                        self.assertEquals(line_id.account_id.code,
                                          self.vendor_bill_obj.
                                          invoice_line_ids[0].account_id.code)
                    else:
                        self.assertEquals(line_id.account_id.id,
                                          self.company_a.
                                          due_from_account_id.id)

        note_wizard = self.env['account.invoice.refund'].\
            with_context(active_ids=[self.vendor_bill_obj.id]).create({
                'reason': 'Testing',
                'filter_refund': 'cancel'
            })
        note_wizard.compute_refund('cancel')
