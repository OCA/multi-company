# -*- coding: utf-8 -*-
# © 2013-Today Odoo SA
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.exceptions import Warning as UserError
from openerp.tests.common import TransactionCase


class TestPurchaseSaleInterCompany(TransactionCase):
    def setUp(self):
        super(TestPurchaseSaleInterCompany, self).setUp()
        self.purchase = self.env.ref(
            'purchase_sale_inter_company.purchase_company_a')
        self.sales_company = self.env.ref(
            'account_invoice_inter_company.company_b')

    def test_01_purchase_sale_inter_company_validated(self):
        purchase_price = self.purchase.order_line.price_unit
        self.sales_company.write({
            'sale_auto_validation': True,
            'update_intercompany_purchase_price': True,
        })
        # Confirm the purchase of company A
        self.purchase.sudo(self.env.ref(
            'account_invoice_inter_company.user_company_a')).signal_workflow(
                'purchase_confirm')
        # Check sale order created in company B
        sales = self.env['sale.order'].sudo(self.env.ref(
            'account_invoice_inter_company.user_company_b')).search([
                ('auto_purchase_order_id', '=', self.purchase.id)
            ])
        self.assertTrue(sales)
        self.assertEquals(len(sales), 1)
        self.assertEquals(sales.state, 'manual')
        self.assertEquals(sales.partner_id,
                          self.purchase.company_id.partner_id)
        self.assertEquals(sales.company_id.partner_id,
                          self.purchase.partner_id)
        self.assertEquals(len(sales.order_line),
                          len(self.purchase.order_line))
        self.assertEquals(sales.order_line.product_id,
                          self.purchase.order_line.product_id)
        # Price has been updated
        self.assertNotEqual(
            purchase_price, self.purchase.order_line.price_unit)
        self.assertEqual(
            sales.order_line.price_unit, self.purchase.order_line.price_unit)
        # Price update is logged on the purchase order
        term = "%s -&gt; %s" % (
            purchase_price, sales.order_line.price_unit)
        self.assertIn(term, ''.join(self.purchase.message_ids.mapped('body')))

    def test_02_purchase_sale_inter_company_draft(self):
        self.sales_company.write({
            'sale_auto_validation': False,
            'update_intercompany_purchase_price': True,
        })
        # Confirm the purchase of company A
        self.purchase.sudo(self.env.ref(
            'account_invoice_inter_company.user_company_a')).signal_workflow(
                'purchase_confirm')
        # Check sale order created in company B
        sales = self.env['sale.order'].sudo(self.env.ref(
            'account_invoice_inter_company.user_company_b')).search([
                ('auto_purchase_order_id', '=', self.purchase.id)
            ])
        self.assertTrue(sales)
        self.assertEquals(sales.state, 'draft')

    def test_03_purchase_sale_inter_company_no_price_update(self):
        self.sales_company.write({
            'sale_auto_validation': True,
            'update_intercompany_purchase_price': False,
        })
        # Confirm the purchase of company A
        with self.assertRaisesRegexp(UserError, 'price difference'):
            self.purchase.sudo(self.env.ref(
                'account_invoice_inter_company.user_company_a')
            ).signal_workflow('purchase_confirm')
