# -*- coding: utf-8 -*-
# Copyright 2013-2014 Odoo SA
# Copyright 2015-2018 Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestPurchaseSaleInterCompany(TransactionCase):
    def setUp(self):
        super(TestPurchaseSaleInterCompany, self).setUp()
        self.purchase_company_a = self.env.ref(
            'purchase_sale_inter_company.purchase_company_a')

        # Fix default value of company_id set by the company_ids field
        # of base_multi_company module
        if self.purchase_company_a.partner_id.company_ids:
            self.purchase_company_a.partner_id.company_ids = [(6, 0, [])]
        for line in self.purchase_company_a.order_line:
            if line.product_id.company_ids:
                line.product_id.company_ids = [(6, 0, [])]

    def test_purchase_sale_inter_company(self):
        # Confirm the purchase of company A
        self.purchase_company_a.sudo(self.env.ref(
            'account_invoice_inter_company.user_company_a')).button_confirm()

        # Check sale order created in company B
        sales = self.env['sale.order'].sudo(self.env.ref(
            'account_invoice_inter_company.user_company_b')).search([
                ('auto_purchase_order_id', '=', self.purchase_company_a.id)
            ])
        self.assertNotEquals(sales, False)
        self.assertEquals(len(sales), 1)
        if sales.company_id.sale_auto_validation:
            self.assertEquals(sales.state, 'sale')
        else:
            self.assertEquals(sales.state, 'draft')
        self.assertEquals(sales.partner_id,
                          self.purchase_company_a.company_id.partner_id)
        self.assertEquals(sales.company_id.partner_id,
                          self.purchase_company_a.partner_id)
        self.assertEquals(len(sales.order_line),
                          len(self.purchase_company_a.order_line))
        self.assertEquals(sales.order_line.product_id,
                          self.purchase_company_a.order_line.product_id)
