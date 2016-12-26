# -*- coding: utf-8 -*-
# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common
from odoo.exceptions import AccessError


@common.at_install(False)
@common.post_install(True)
class TestProductMultiCompany(common.TransactionCase):
    def setUp(self):
        super(TestProductMultiCompany, self).setUp()
        self.group_user = self.env.ref('base.group_user')
        self.env.ref('product.access_product_product_employee').write({
            'perm_write': True,
            'perm_read': True,
            'perm_create': True,
            'perm_unlink': True,
        })
        self.env.ref('product.access_product_template_user').write({
            'perm_write': True,
            'perm_read': True,
            'perm_create': True,
            'perm_unlink': True,
        })
        self.company_1 = self.env['res.company'].create(
            {'name': 'Test company 1'}
        )
        self.company_2 = self.env['res.company'].create(
            {'name': 'Test company 2'}
        )
        self.product_company_none = self.env['product.product'].create(
            {'name': 'Product without company',
             'company_ids': [(6, 0, [])],
             'company_id': False})
        self.product_company_1 = self.env['product.product'].create(
            {'name': 'Product from company 1',
             'company_ids': [(6, 0, self.company_1.ids)]})
        self.product_company_2 = self.env['product.product'].create(
            {'name': 'Product from company 2',
             'company_ids': [(6, 0, self.company_2.ids)]})
        self.product_company_both = self.env['product.product'].create(
            {'name': 'Product for both companies',
             'company_ids': [(6, 0, (self.company_1 + self.company_2).ids)]})
        self.user_company_1 = self.env['res.users'].create(
            {'name': 'User company 1',
             'login': 'user_company_1',
             'groups_id': [
                 (6, 0, self.group_user.ids)],
             'company_id': self.company_1.id,
             'company_ids': [(6, 0, self.company_1.ids)]})
        self.user_company_2 = self.env['res.users'].create(
            {'name': 'User company 2',
             'login': 'user_company_2',
             'groups_id': [
                 (6, 0, self.group_user.ids)],
             'company_id': self.company_2.id,
             'company_ids': [(6, 0, self.company_2.ids)]})

    def test_create_product(self):
        product = self.env['product.product'].create({'name': 'Test'})
        company = self.env['res.company']._company_default_get(
            'product.template')
        self.assertTrue(company.id in product.company_ids.ids)

    def test_company_none(self):
        self.assertFalse(self.product_company_none.company_id)
        # All of this should be allowed
        self.product_company_none.sudo(self.user_company_1.id).name = "Test"
        self.product_company_none.sudo(self.user_company_2.id).name = "Test"

    def test_company_1(self):
        self.assertEqual(
            self.product_company_1.sudo(self.user_company_1).company_id,
            self.company_1,
        )
        # All of this should be allowed
        self.product_company_1.sudo(self.user_company_1).name = "Test"
        self.product_company_both.sudo(self.user_company_1).name = "Test"
        # And this one not
        with self.assertRaises(AccessError):
            self.product_company_2.sudo(self.user_company_1).name = "Test"

    def test_company_2(self):
        self.assertEqual(
            self.product_company_2.sudo(self.user_company_2).company_id,
            self.company_2,
        )
        # All of this should be allowed
        self.product_company_2.sudo(self.user_company_2).name = "Test"
        self.product_company_both.sudo(self.user_company_2).name = "Test"
        # And this one not
        with self.assertRaises(AccessError):
            self.product_company_1.sudo(self.user_company_2).name = "Test"

    def test_uninstall(self):
        from ..hooks import uninstall_hook
        uninstall_hook(self.env.cr, None)
        rule = self.env.ref('product.product_comp_rule')
        domain = (" ['|', ('company_id', '=', user.company_id.id), "
                  "('company_id', '=', False)]")
        self.assertEqual(rule.domain_force, domain)
