# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestAccountInvoiceInterCompany(TransactionCase):
    def setUp(self):
        super(TestAccountInvoiceInterCompany, self).setUp()
        self.wizard_obj = self.env['wizard.multi.charts.accounts']
        self.account_obj = self.env['account.account']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_company_a = self.env.ref(
            'account_invoice_inter_company.customer_invoice_company_a')
        self.user_company_a = self.env.ref(
            'account_invoice_inter_company.user_company_a')
        self.user_company_b = self.env.ref(
            'account_invoice_inter_company.user_company_b')

    def test_account_invoice_inter_company(self):
        # Install COA for company A and B
        wizard_comp_a = self.wizard_obj.create({
            'company_id': self.env.ref(
                'account_invoice_inter_company.company_a').id,
            'chart_template_id': '1',
            'code_digits': 6,
            'transfer_account_id': self.env.ref(
                'account_invoice_inter_company.pcg_X58_a').id,
            'currency_id': self.env.ref('base.EUR').id,
            'bank_account_code_prefix': False,
            'cash_account_code_prefix': False,
        })
        wizard_comp_a.onchange_chart_template_id()
        wizard_comp_a.execute()
        wizard_comp_b = self.wizard_obj.create({
            'company_id': self.env.ref(
                'account_invoice_inter_company.company_b').id,
            'chart_template_id': '1',
            'code_digits': 6,
            'transfer_account_id': self.env.ref(
                'account_invoice_inter_company.pcg_X58_b').id,
            'currency_id': self.env.ref('base.EUR').id,
            'bank_account_code_prefix': False,
            'cash_account_code_prefix': False,
        })
        wizard_comp_b.onchange_chart_template_id()
        wizard_comp_b.execute()

        # Fix default value of company_id set by the company_ids field
        # of base_multi_company module
        if self.invoice_company_a.partner_id.company_ids:
            self.invoice_company_a.partner_id.company_ids = [(6, 0, [])]
        for line in self.invoice_company_a.invoice_line_ids:
            if line.product_id.company_ids:
                line.product_id.company_ids = [(6, 0, [])]

        # Confirm the invoice of company A
        self.invoice_company_a.sudo(
            self.user_company_a.id).action_invoice_open()

        # Check destination invoice created in company B
        invoices = self.invoice_obj.sudo(self.user_company_b.id).search([
            ('auto_invoice_id', '=', self.invoice_company_a.id)
        ])
        self.assertNotEquals(invoices, False)
        self.assertEquals(len(invoices), 1)
        if invoices.company_id.invoice_auto_validation:
            self.assertEquals(invoices[0].state, 'open')
        else:
            self.assertEquals(invoices[0].state, 'draft')
        self.assertEquals(invoices[0].partner_id,
                          self.invoice_company_a.company_id.partner_id)
        self.assertEquals(invoices[0].company_id.partner_id,
                          self.invoice_company_a.partner_id)
        self.assertEquals(len(invoices[0].invoice_line_ids),
                          len(self.invoice_company_a.invoice_line_ids))
        self.assertEquals(
            invoices[0].invoice_line_ids[0].product_id,
            self.invoice_company_a.invoice_line_ids[0].product_id)
