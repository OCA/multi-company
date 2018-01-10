# -*- coding: utf-8 -*-
# © 2015-2017 Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo import _


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

        # Install COA for company A and B
        wizard_comp_a = self.wizard_obj.create({
            'company_id': self.env.ref(
                'account_invoice_inter_company.company_a').id,
            'chart_template_id': 1,
            'code_digits': 6,
            'transfer_account_id': self.env.ref(
                'account_invoice_inter_company.pcg_X58').id,
            'currency_id': self.env.ref('base.EUR').id,
            'bank_account_code_prefix': False,
            'cash_account_code_prefix': False,
        })
        wizard_comp_a.onchange_chart_template_id()
        wizard_comp_a.execute()
        wizard_comp_b = self.wizard_obj.create({
            'company_id': self.env.ref(
                'account_invoice_inter_company.company_b').id,
            'chart_template_id': 1,
            'code_digits': 6,
            'transfer_account_id': self.env.ref(
                'account_invoice_inter_company.pcg_X58').id,
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

    def test01_user(self):
        # Check user of company B (company of destination)
        # with which we check the intercompany product
        self.assertNotEquals(self.user_company_b.id, 1)
        dest_company = self.env['res.company']._find_company_from_partner(
            self.invoice_company_a.partner_id.id)
        self.assertEquals(self.user_company_b.company_id, dest_company)
        self.assertIn(
            self.user_company_b.id,
            self.env.ref('account.group_account_invoice').users.ids)

    def test02_product(self):
        # Check product is intercompany
        for line in self.invoice_company_a.invoice_line_ids:
            self.assertFalse(line.product_id.company_id)

    def test03_confirm_invoice(self):
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

    def test04_cancel_invoice(self):
        # Confirm the invoice of company A
        self.invoice_company_a.sudo(
            self.user_company_a.id).action_invoice_open()
        # Check state of invoices before to cancel invoice of company A
        self.assertEquals(self.invoice_company_a.state, 'open')
        invoices = self.invoice_obj.sudo(self.user_company_b.id).search([
            ('auto_invoice_id', '=', self.invoice_company_a.id)
        ])
        self.assertNotEquals(invoices[0].state, 'cancel')
        # Cancel the invoice of company A
        origin = _('%s - Canceled Invoice: %s') % (
            self.invoice_company_a.company_id.name,
            self.invoice_company_a.number)
        self.invoice_company_a.sudo(
            self.user_company_a.id).action_invoice_cancel()
        # Check invoices after to cancel invoice of company A
        self.assertEquals(self.invoice_company_a.state, 'cancel')
        self.assertEquals(invoices[0].state, 'cancel')
        self.assertEquals(invoices[0].origin, origin)
