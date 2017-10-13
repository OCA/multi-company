# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestAccountInvoiceInterCompany(TransactionCase):
    def setUp(self):
        super(TestAccountInvoiceInterCompany, self).setUp()
        self.wizard_obj = self.env['wizard.multi.charts.accounts']
        self.account_obj = self.env['account.account']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_company_a = self.env.ref(
            'account_invoice_inter_company.customer_invoice_company_a')

    def test_account_invoice_inter_company(self):
        # Install COA for company A and B
        wizard_comp_a = self.wizard_obj.create({
            'company_id': self.env.ref('account_invoice_inter_company.company_a').id,
            'chart_template_id': self.env.ref('l10n_fr.l10n_fr_pcg_chart_template').id,
            'code_digits': 6,
            'transfer_account_id': self.env.ref('l10n_fr.pcg_58').id,
            'currency_id': self.env.ref('base.EUR').id,
            'bank_account_code_prefix': False,
            'cash_account_code_prefix': False,
        })
        wizard_comp_a.onchange_chart_template_id()
        wizard_comp_a.execute()
        wizard_comp_b = self.wizard_obj.create({
            'company_id': self.env.ref('account_invoice_inter_company.company_b').id,
            'chart_template_id': self.env.ref('l10n_fr.l10n_fr_pcg_chart_template').id,
            'code_digits': 6,
            'transfer_account_id': self.env.ref('l10n_fr.pcg_58').id,
            'currency_id': self.env.ref('base.EUR').id,
            'bank_account_code_prefix': False,
            'cash_account_code_prefix': False,
        })
        wizard_comp_b.onchange_chart_template_id()
        wizard_comp_b.execute()

        ## Now remove company from related partners of company and
        ## apply default accounts
        #account_receivable_a = self.account_obj.search([
        #    ('company_id', '=', self.env.ref(
        #        'account_invoice_inter_company.company_a').id),
        #    ('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)
        #])
        #account_payable_a = self.account_obj.search([
        #    ('company_id', '=', self.env.ref(
        #        'account_invoice_inter_company.company_a').id),
        #    ('user_type_id', '=', self.env.ref('account.data_account_type_payable').id)
        #])
        #import pdb;pdb.set_trace()
        #self.env.ref('account_invoice_inter_company.partner_company_a').write({
        #    'company_id': False,
        #    'property_account_receivable_id': account_receivable_a[0].id,
        #    'property_account_payable_id': account_payable_a[0].id
        #})
        #
        #account_receivable_b = self.account_obj.search([
        #    ('company_id', '=', self.env.ref(
        #        'account_invoice_inter_company.company_b').id),
        #    ('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)
        #])
        #account_payable_b = self.account_obj.search([
        #    ('company_id', '=', self.env.ref(
        #        'account_invoice_inter_company.company_b').id),
        #    ('user_type_id', '=', self.env.ref('account.data_account_type_payable').id)
        #])
        #self.env.ref('account_invoice_inter_company.partner_company_b').write({
        #    'company_id': False,
        #    'property_account_receivable_id': account_receivable_b[0].id,
        #    'property_account_payable_id': account_payable_b[0].id
        #})

        # Confirm the invoice of company A
        self.invoice_company_a.sudo(self.env.ref(
            'account_invoice_inter_company.user_company_a')).action_invoice_open()

        # Check destination invoice created in company B
        invoices = self.invoice_obj.sudo(self.env.ref(
            'account_invoice_inter_company.user_company_b')).search([
                ('auto_invoice_id', '=', self.invoice_company_a.id)
            ])
        self.assertNotEquals(invoices, False)
        self.assertEquals(len(invoices), 1)
        if invoices.company_id.invoice_auto_validation:
            self.assertEquals(invoices.state, 'open')
        else:
            self.assertEquals(invoices.state, 'draft')
        self.assertEquals(invoices.partner_id,
                          self.invoice_company_a.company_id.partner_id)
        self.assertEquals(invoices.company_id.partner_id,
                          self.invoice_company_a.partner_id)
        self.assertEquals(len(invoices.invoice_line),
                          len(self.invoice_company_a.invoice_line))
        self.assertEquals(invoices.invoice_line.product_id,
                          self.invoice_company_a.invoice_line.product_id)
