# -*- coding: utf-8 -*-
# Copyright 2013-2014 Odoo SA
# Copyright 2015-2018 Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, UserError


class TestPurchaseSaleInterCompany(TransactionCase):
    def setUp(self):
        super(TestPurchaseSaleInterCompany, self).setUp()
        self.purchase_a = self.env.ref(
            'purchase_sale_inter_company.purchase_company_a')
        self.company_a = self.env.ref(
            'account_invoice_inter_company.company_a')
        self.company_b = self.env.ref(
            'account_invoice_inter_company.company_b')
        self.company_a.sale_auto_validation = True
        self.company_b.sale_auto_validation = True
        self.user_a = self.env.ref(
            'account_invoice_inter_company.user_company_a')
        self.user_b = self.env.ref(
            'account_invoice_inter_company.user_company_b')
        self.product_consultant = self.env.ref(
            'account_invoice_inter_company.product_consultant_multi_company')
        self.account_sale_b = self.env.ref(
            'account_invoice_inter_company.a_sale_company_b')
        self.product_consultant.sudo(
            self.user_b).property_account_income_id = self.account_sale_b

        # Fix default value of company_id set by the company_ids field
        # of base_multi_company module
        if self.purchase_a.partner_id.company_ids:
            self.purchase_a.partner_id.company_ids = [(6, 0, [])]
        if self.company_a.partner_id.company_ids:
            self.company_a.partner_id.company_ids = [(6, 0, [])]
        if self.company_b.partner_id.company_ids:
            self.company_b.partner_id.company_ids = [(6, 0, [])]
        for line in self.purchase_a.order_line:
            if line.product_id.company_ids:
                line.product_id.company_ids = [(6, 0, [])]

    def test_purchase_sale_inter_company(self):
        # Confirm the purchase of company A
        self.purchase_a.sudo(self.user_a).button_confirm()

        # Check sale order created in company B
        sales = self.env['sale.order'].sudo(self.user_b).search([
            ('auto_purchase_order_id', '=', self.purchase_a.id)
        ])
        self.assertNotEquals(sales, False)
        self.assertEquals(len(sales), 1)
        if sales.company_id.sale_auto_validation:
            self.assertEquals(sales.state, 'sale')
        else:
            self.assertEquals(sales.state, 'draft')
        self.assertEquals(sales.partner_id,
                          self.purchase_a.company_id.partner_id)
        self.assertEquals(sales.company_id.partner_id,
                          self.purchase_a.partner_id)
        self.assertEquals(len(sales.order_line),
                          len(self.purchase_a.order_line))
        self.assertEquals(sales.order_line.product_id,
                          self.purchase_a.order_line.product_id)

    def test_raise_product_access(self):
        product_rule = self.env.ref('product.product_comp_rule')
        product_rule.active = True
        self.product_consultant.company_id = self.company_b
        with self.assertRaises(AccessError):
            self.purchase_a.sudo(self.user_a).button_confirm()

    def test_raise_currency(self):
        currency = self.env.ref('base.XPF')
        self.purchase_a.currency_id = currency
        with self.assertRaises(UserError):
            self.purchase_a.sudo(self.user_a).button_confirm()

    def test_raise_warehouse(self):
        self.company_b.warehouse_id = False
        with self.assertRaises(UserError):
            self.purchase_a.sudo(self.user_a).button_confirm()

    def test_purchase_invoice_relation(self):
        self.purchase_a.sudo(self.user_a).button_confirm()
        sales = self.env['sale.order'].sudo(self.user_b).search([
            ('auto_purchase_order_id', '=', self.purchase_a.id),
        ])
        sales.partner_shipping_id = sales.partner_id.id
        sale_invoice_id = sales.action_invoice_create()[0]
        sale_invoice = self.env['account.invoice'].browse(sale_invoice_id)
        sale_invoice.action_invoice_open()
        self.assertEquals(sale_invoice,
                          self.purchase_a.invoice_ids.auto_invoice_id)
        self.assertEquals(
            sale_invoice.invoice_line_ids,
            self.purchase_a.invoice_ids.auto_invoice_id.invoice_line_ids)

    def test_cancel(self):
        self.purchase_a.sudo(self.user_a).button_confirm()
        sales = self.env['sale.order'].sudo(self.user_b).search([
            ('auto_purchase_order_id', '=', self.purchase_a.id)
        ])
        self.assertEquals(self.purchase_a.partner_ref, sales.name)
        self.purchase_a.sudo(self.user_a).button_cancel()
        self.assertFalse(self.purchase_a.partner_ref)
