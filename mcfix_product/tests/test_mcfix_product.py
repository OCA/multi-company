# -*- coding: utf-8 -*-
# Copyright 2017 Creu Blanca.
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests import common
from odoo import exceptions


class TestMcfixProduct(common.TransactionCase):

    def setUp(self):
        super(TestMcfixProduct, self).setUp()
        self.res_users_model = self.env['res.users']
        self.group_user = self.env.ref('base.group_user')
        self.company_1 = self.env['res.company'].create(
            {'name': 'Test company 1'}
        )
        self.company_2 = self.env['res.company'].create(
            {'name': 'Test company 2'}
        )

        self.partner_1 = self.env['res.partner'].create({
            'name': 'Supplier',
            'supplier': True,
            'company_id': self.company_1.id
        })

        # Create user_1
        self.user_1 =\
            self.res_users_model.with_context({'no_reset_password': True}).\
            create({
                'name': 'Test User',
                'login': 'user_1',
                'password': 'demo',
                'email': 'example@yourcompany.com',
                'company_id': self.company_1.id,
                'company_ids': [(4, self.company_1.id),
                                (4, self.company_2.id)],
                'groups_id': [(6, 0, [self.group_user.id])]
            })

    def test_product_category(self):
        product_category = self.env['product.category'].create(
            {'name': 'Test'})
        self.assertEquals(product_category.sudo(
            self.user_1).current_company_id, self.user_1.company_id)
        self.assertEquals(product_category.sudo(
            self.user_1).with_context(
            force_company=self.company_2.id).current_company_id, self.company_2)

    def test_product_template(self):
        product_template = self.env['product.template'].create(
            {'name': 'Test'})
        self.assertEquals(product_template.sudo(
            self.user_1).current_company_id, self.user_1.company_id)
        self.assertEquals(product_template.sudo(
            self.user_1).with_context(
            force_company=self.company_2.id).current_company_id, self.company_2)

    def test_product_supplierinfo_1(self):
        product_product = self.env['product.product'].create(
            {'name': 'Test',
             'company_id': self.company_1.id})
        with self.assertRaises(exceptions.ValidationError):
            self.env['product.supplierinfo'].create(
                {'product_id': product_product.id,
                 'name': self.partner_1.id,
                 'company_id': self.company_2.id})

    def test_product_supplierinfo_2(self):
        product_product = self.env['product.product'].create(
            {'name': 'Test',
             'company_id': self.company_1.id})
        self.partner_1.company_id = self.company_2
        with self.assertRaises(exceptions.ValidationError):
            self.env['product.supplierinfo'].create(
                {'product_id': product_product.id,
                 'name': self.partner_1.id,
                 'company_id': self.company_1.id})
