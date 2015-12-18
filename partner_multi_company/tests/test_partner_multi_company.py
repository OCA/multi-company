# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.tests import common
from openerp.osv.osv import except_orm as AccessError


class TestProductMultiCompany(common.TransactionCase):
    def setUp(self):
        super(TestProductMultiCompany, self).setUp()
        self.env.user.write({
            'groups_id': [
                (6, 0, self.env.ref('base.group_partner_manager').ids)],
        })
        self.company_1 = self.env['res.company'].create(
            {'name': 'Test company 1'})
        self.company_2 = self.env['res.company'].create(
            {'name': 'Test company 2'})
        self.partner_company_none = self.env['res.partner'].create(
            {'name': 'partner without company',
             'company_ids': [(6, 0, [])]})
        self.partner_company_1 = self.env['res.partner'].create(
            {'name': 'partner from company 1',
             'company_ids': [(6, 0, self.company_1.ids)]})
        self.partner_company_2 = self.env['res.partner'].create(
            {'name': 'partner from company 2',
             'company_ids': [(6, 0, self.company_2.ids)]})
        self.partner_company_both = self.env['res.partner'].create(
            {'name': 'partner for both companies',
             'company_ids': [(6, 0, (self.company_1 + self.company_2).ids)]})
        self.user_company_1 = self.env['res.users'].create(
            {'name': 'User company 1',
             'login': 'user_company_1',
             'groups_id': [
                 (6, 0, self.env.ref('base.group_partner_manager').ids)],
             'company_id': self.company_1.id,
             'company_ids': [(6, 0, self.company_1.ids)]})
        self.user_company_2 = self.env['res.users'].create(
            {'name': 'User company 2',
             'login': 'user_company_2',
             'groups_id': [
                 (6, 0, self.env.ref('base.group_partner_manager').ids)],
             'company_id': self.company_2.id,
             'company_ids': [(6, 0, self.company_2.ids)]})

    def test_create_partner(self):
        partner = self.env['res.partner'].create({'name': 'Test'})
        company_id = (
            self.env['res.company']._company_default_get('res.partner'))
        self.assertTrue(company_id in partner.company_ids.ids)

    def test_company_none(self):
        self.assertFalse(self.partner_company_none.company_id)
        # All of this should be allowed
        self.partner_company_none.sudo(self.user_company_1.id).name = "Test"
        self.partner_company_none.sudo(self.user_company_2.id).name = "Test"

    def test_company_1(self):
        self.assertEqual(self.partner_company_1.company_id, self.company_1)
        # All of this should be allowed
        self.partner_company_1.sudo(self.user_company_1).name = "Test"
        self.partner_company_both.sudo(self.user_company_1).name = "Test"
        # And this one not
        with self.assertRaises(AccessError):
            self.partner_company_2.sudo(self.user_company_1).name = "Test"

    def test_company_2(self):
        self.assertEqual(self.partner_company_2.company_id, self.company_2)
        # All of this should be allowed
        self.partner_company_2.sudo(self.user_company_2).name = "Test"
        self.partner_company_both.sudo(self.user_company_2).name = "Test"
        # And this one not
        with self.assertRaises(AccessError):
            self.partner_company_1.sudo(self.user_company_2).name = "Test"

    def test_uninstall(self):
        from openerp.addons.partner_multi_company.hooks import uninstall_hook
        uninstall_hook(self.env.cr, None)
        rule = self.env.ref('base.res_partner_rule')
        domain = ("['|','|',"
                  "('company_id.child_ids','child_of',[user.company_id.id]),"
                  "('company_id','child_of',[user.company_id.id]),"
                  "('company_id','=',False)]")
        self.assertEqual(rule.domain_force, domain)
