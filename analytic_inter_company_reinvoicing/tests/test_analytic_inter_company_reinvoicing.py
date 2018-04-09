# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import SavepointCase
from openerp.exceptions import UserError


class TestAnalyticInterCompanyReinvoicing(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAnalyticInterCompanyReinvoicing, cls).setUpClass()
        cls.Account = cls.env['account.account']
        cls.AccountType = cls.env['account.account.type']
        cls.AccountInstaller = cls.env['account.installer']
        cls.AnalyticAccount = cls.env['account.analytic.account']
        cls.AnalyticJournal = cls.env['account.analytic.journal']
        cls.AnalyticReinvoicing = cls.env[
            'account.invoice.analytic.reinvoicing']
        cls.Invoice = cls.env['account.invoice']
        cls.InvoiceLine = cls.env['account.invoice.line']
        cls.MultiChartAccount = cls.env['wizard.multi.charts.accounts']
        cls.Tax = cls.env['account.tax']

        cls.currency_eur = cls.env.ref('base.EUR')
        cls.currency_usd = cls.env.ref('base.USD')

        cls.supplier_asustek = cls.env.ref('base.res_partner_1')

        cls.company_a = cls.env.ref(
            'account_invoice_inter_company.company_a')
        cls.company_b = cls.env.ref(
            'account_invoice_inter_company.company_b')

        cls.account_comp_a_rec = cls.env.ref(
            'account_invoice_inter_company.a_recv_company_a')
        cls.account_comp_b_rec = cls.env.ref(
            'account_invoice_inter_company.a_recv_company_b')

        cls.account_comp_a_inc = cls.env.ref(
            'account_invoice_inter_company.a_sale_company_a')
        cls.account_comp_b_inc = cls.env.ref(
            'account_invoice_inter_company.a_sale_company_b')

        cls.account_comp_a_pay = cls.env.ref(
            'account_invoice_inter_company.a_pay_company_a')
        cls.account_comp_b_pay = cls.env.ref(
            'account_invoice_inter_company.a_pay_company_b')

        cls.account_comp_a_exp = cls.env.ref(
            'account_invoice_inter_company.a_expense_company_a')
        cls.account_comp_b_exp = cls.env.ref(
            'account_invoice_inter_company.a_expense_company_b')

        cls.account_type_other = cls.AccountType.create({
            'name': "Other",
            'code': 'other',
            'close_method': 'none',
            'report_type': 'none',
        })

        cls.account_comp_a_reinvoicing = cls.Account.create({
            'name': "Reinvoicing Account",
            'code': 'RE-INV',
            'type': 'other',
            'user_type': cls.account_type_other.id,
            'company_id': cls.company_a.id,
            'reconcile': True,
        })

        cls.tax_10_p_comp_a = cls.Tax.create({
            'sequence': 30,
            'name': 'Tax 10.0% (Percentage of Price)',
            'amount': 0.1,
            'type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
            'company_id': cls.company_a.id,
        })

        cls.tax_10_p_comp_b = cls.Tax.create({
            'sequence': 30,
            'name': 'Tax 10.0% (Percentage of Price)',
            'amount': 0.1,
            'type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
            'company_id': cls.company_b.id,
        })

        cls.tax_15_p_comp_a = cls.Tax.create({
            'sequence': 30,
            'name': 'Tax 15.0% (Percentage of Price)',
            'amount': 0.15,
            'type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
            'company_id': cls.company_a.id,
        })

        cls.tax_15_p_comp_b = cls.Tax.create({
            'sequence': 30,
            'name': 'Tax 15.0% (Percentage of Price)',
            'amount': 0.15,
            'type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
            'company_id': cls.company_b.id,
        })

        cls.product_5 = cls.env.ref('product.product_product_5')
        cls.product_5.write({
            'company_id': False,
            'standard_price': 1000,
            'list_price': 500,
            'taxes_id': [(6, 0, [
                cls.tax_10_p_comp_a.id, cls.tax_10_p_comp_b.id
            ])],
        })
        cls.product_5.with_context(force_company=cls.company_a.id).write({
            'property_account_income': cls.account_comp_a_inc.id,
            'property_account_expense': cls.account_comp_a_exp.id,
        })
        cls.product_5.with_context(force_company=cls.company_b.id).write({
            'property_account_income': cls.account_comp_b_inc.id,
            'property_account_expense': cls.account_comp_b_exp.id,
        })

        cls.product_6 = cls.env.ref('product.product_product_6')
        cls.product_6.write({
            'company_id': False,
            'standard_price': 1000,
            'list_price': 500,
            'taxes_id': [(6, 0, [
                cls.tax_10_p_comp_a.id, cls.tax_15_p_comp_a.id,
                cls.tax_10_p_comp_b.id, cls.tax_15_p_comp_b.id,
            ])],
        })
        cls.product_6.with_context(force_company=cls.company_a.id).write({
            'property_account_income': cls.account_comp_a_inc.id,
            'property_account_expense': cls.account_comp_a_exp.id,
        })
        cls.product_6.with_context(force_company=cls.company_b.id).write({
            'property_account_income': cls.account_comp_b_inc.id,
            'property_account_expense': cls.account_comp_b_exp.id,
        })

        cls.company_a.write({
            'currency_id': cls.currency_eur.id,
            'reinvoice_waiting_account_id': cls.account_comp_a_reinvoicing.id,
        })
        cls.company_b.write({
            'currency_id': cls.currency_usd.id,
        })

        cls.comp_a_test_aa = cls.AnalyticAccount.create({
            'name': "Test",
            'company_id': cls.company_a.id,
        })

        cls.comp_b_test_aa = cls.AnalyticAccount.create({
            'name': "Test 2",
            'company_id': cls.company_b.id,
            'currency_id': cls.currency_usd.id,
        })

        cls.comp_b_purchase_journal = cls.env.ref(
            'account_invoice_inter_company.purchases_journal_company_b')
        cls.comp_b_purchase_analytic_journal = cls.AnalyticJournal.create({
            'name': "Purchase",
            'code': "P",
            'type': 'purchase',
            'company_id': cls.company_b.id,
        })
        cls.comp_b_purchase_journal.write({
            'analytic_journal_id': cls.comp_b_purchase_analytic_journal.id,
        })

        cls.supplier_asustek.with_context(
            force_company=cls.company_a.id
        ).write({
            'property_account_payable': cls.account_comp_a_pay.id,
        })

    def create_supplier_invoice(self, supplier, company):
        supplier = supplier.with_context(force_company=company.id)
        values = {
            'partner_id': supplier.id,
            'account_id': supplier.property_account_payable.id,
            'company_id': company.id,
            'type': 'in_invoice',
        }
        return self.Invoice.create(values)

    def add_invoice_line(self, invoice, product, qty):
        values = {
            'invoice_id': invoice.id,
            'product_id': product.id,
            'name': product.name,
            'quantity': qty,
            'invoice_line_tax_id': [(6, 0, [
                self.tax_10_p_comp_a.id,
                self.tax_15_p_comp_a.id,
            ])]
        }
        line = self.InvoiceLine.with_context(
            force_company=invoice.company_id.id
        ).create(values)
        update_values = line.product_id_change(
            product.id,
            product.uom_id.id,
            partner_id=invoice.partner_id.id
        )['value']
        update_values.update({
            'account_id': product.property_account_expense.id,
        })
        line.write(update_values)
        return line

    def test_onchange_reinvoice_analytic_account(self):
        partner = self.supplier_asustek
        company = self.company_a

        product = self.product_5.with_context(force_company=company.id)
        invoice = self.create_supplier_invoice(partner, company)
        inv_line_1 = self.add_invoice_line(invoice, product, 1)

        inv_line_1.reinvoice_analytic_account_id = self.comp_a_test_aa
        inv_line_1._onchange_reinvoice_analytic_account()
        self.assertEqual(
            inv_line_1.account_id,
            company.reinvoice_waiting_account_id)

    def test_analytic_reinvoicing_wizard_invoice_creation(self):
        partner = self.supplier_asustek
        company = self.company_a
        invoice = self.create_supplier_invoice(partner, company)
        product = self.product_5.with_context(force_company=company.id)

        inv_line_1 = self.add_invoice_line(invoice, product, 1)
        inv_line_1.reinvoice_analytic_account_id = self.comp_b_test_aa
        inv_line_1._onchange_reinvoice_analytic_account()
        inv_line_2 = self.add_invoice_line(invoice, product, 1)

        invoice.signal_workflow('invoice_open')

        wizard = self.AnalyticReinvoicing.create({
            'company_id': self.company_a.id,
        })
        invoice_lines_by_company = wizard.get_lines_to_reinvoice_by_company()

        self.assertEqual(
            invoice_lines_by_company,
            {
                self.company_b: inv_line_1,
            }
        )
        self.assertTrue(
            inv_line_2 not in invoice_lines_by_company[self.company_b])

        new_invoice = wizard.create_invoice_for_company(
            self.company_b, inv_line_1)
        self.assertEqual(new_invoice.partner_id, self.company_b.partner_id)
        self.assertEqual(new_invoice.currency_id, self.currency_usd)

        # reinvoice_line_id has been updated on the source move line
        # so we should not be able to update/delete it
        with self.assertRaises(UserError), self.env.cr.savepoint():
            inv_line_1.unlink()

        with self.assertRaises(UserError), self.env.cr.savepoint():
            inv_line_1.write({'name': "Test"})

        self.assertEqual(len(new_invoice.invoice_line), 1)
        self.assertEqual(
            inv_line_1.reinvoice_line_id,
            new_invoice.invoice_line[0])

    def test_analytic_reinvoicing(self):
        partner = self.supplier_asustek
        company = self.company_a
        invoice = self.create_supplier_invoice(partner, company)
        product = self.product_6.with_context(force_company=company.id)

        inv_line_1 = self.add_invoice_line(invoice, product, 1)
        inv_line_1.reinvoice_analytic_account_id = self.comp_b_test_aa
        inv_line_1._onchange_reinvoice_analytic_account()
        self.add_invoice_line(invoice, product, 1)

        invoice.signal_workflow('invoice_open')

        wizard = self.AnalyticReinvoicing.create({
            'company_id': self.company_a.id,
        })
        domain = wizard.execute()['domain']

        new_invoice = self.Invoice.search(domain)
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(new_invoice.type, 'out_invoice')
        self.assertEqual(new_invoice.currency_id, self.currency_usd)

        comp_b_invoice = self.Invoice.search([
            ('company_id', '=', self.company_b.id),
            ('type', '=', 'in_invoice'),
            ('origin', 'ilike', new_invoice.number),
        ])
        self.assertEqual(len(comp_b_invoice), 1)

        comp_b_invoice_line = comp_b_invoice.invoice_line
        self.assertEqual(len(comp_b_invoice_line), 1)

        self.assertEqual(
            comp_b_invoice_line.account_analytic_id,
            self.comp_b_test_aa)
