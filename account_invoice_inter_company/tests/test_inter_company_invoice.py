# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestAccountInvoiceInterCompany(TransactionCase):
    def setUp(self):
        super(TestAccountInvoiceInterCompany, self).setUp()
        self.installer_obj = self.env['account.installer']
        self.wizard_obj = self.env['wizard.multi.charts.accounts']
        self.account_obj = self.env['account.account']
        self.invoice_obj = self.env['account.invoice']
        self.invoice_company_a = self.env.ref(
            'account_invoice_inter_company.customer_invoice_company_a')

    def test_account_invoice_inter_company(self):
        # Install COA for company A and B
        installer_comp_a = self.installer_obj.create({
            'charts': 'configurable',
            'company_id': self.env.ref(
                'account_invoice_inter_company.company_a').id})
        installer_comp_a.execute()
        installer_comp_b = self.installer_obj.create({
            'charts': 'configurable',
            'company_id': self.env.ref(
                'account_invoice_inter_company.company_b').id})
        installer_comp_b.execute()

        wiz_comp_a = self.wizard_obj.create({
            'chart_template_id': '1',
            'company_id': self.env.ref(
                'account_invoice_inter_company.company_a').id,
            'currency_id': self.env.ref('base.EUR').id,
            'code_digits': 6,
            'purchase_tax': False,
            'sale_tax': False})
        wiz_comp_a.execute()
        wiz_comp_b = self.wizard_obj.create({
            'chart_template_id': '1',
            'company_id': self.env.ref(
                'account_invoice_inter_company.company_b').id,
            'currency_id': self.env.ref('base.EUR').id,
            'code_digits': 6,
            'purchase_tax': False,
            'sale_tax': False})
        wiz_comp_b.execute()

        # Now remove company from related partners of company and
        # apply default accounts
        account_receivable_a = self.account_obj.search([
            ('company_id', '=', self.env.ref(
                'account_invoice_inter_company.company_a').id),
            ('type', '=', 'receivable')
        ])
        account_payable_a = self.account_obj.search([
            ('company_id', '=', self.env.ref(
                'account_invoice_inter_company.company_a').id),
            ('type', '=', 'payable')
        ])
        self.env.ref('account_invoice_inter_company.partner_company_a').write({
            'company_id': False,
            'property_account_receivable': account_receivable_a[0],
            'property_account_payable': account_payable_a[0]
        })

        account_receivable_b = self.account_obj.search([
            ('company_id', '=', self.env.ref(
                'account_invoice_inter_company.company_b').id),
            ('type', '=', 'receivable')
        ])
        account_payable_b = self.account_obj.search([
            ('company_id', '=', self.env.ref(
                'account_invoice_inter_company.company_b').id),
            ('type', '=', 'payable')
        ])
        self.env.ref('account_invoice_inter_company.partner_company_b').write({
            'company_id': False,
            'property_account_receivable': account_receivable_b[0],
            'property_account_payable': account_payable_b[0]
        })

        # Confirm the invoice of company A
        self.invoice_company_a.sudo(self.env.ref(
            'account_invoice_inter_company.user_company_a')).signal_workflow(
                'invoice_open')

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
