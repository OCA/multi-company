# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui
# © 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.tests import common
from openerp.osv.osv import except_orm as AccessError


class TestPartnerMultiCompany(common.TransactionCase):
    def setUp(self):
        super(TestPartnerMultiCompany, self).setUp()
        # This is for being sure that the suspend_security method is hooked
        self.env['ir.rule']._register_hook()
        # Avoid possible spam
        self.partner_model = self.env['res.partner'].with_context(
            mail_create_nosubscribe=True)
        self.company_1 = self.env['res.company'].create(
            {'name': 'Test company 1'})
        self.company_2 = self.env['res.company'].create(
            {'name': 'Test company 2'})
        self.partner_company_none = self.partner_model.create(
            {'name': 'partner without company',
             'company_ids': False})
        self.partner_company_1 = self.partner_model.create(
            {'name': 'partner from company 1',
             'company_ids': [(6, 0, self.company_1.ids)]})
        self.partner_company_2 = self.partner_model.create(
            {'name': 'partner from company 2',
             'company_ids': [(6, 0, self.company_2.ids)]})
        self.partner_company_both = self.partner_model.create(
            {'name': 'partner for both companies',
             'company_ids': [(6, 0, (self.company_1 + self.company_2).ids)]})
        self.user_company_1 = self.env['res.users'].create(
            {'name': 'User company 1',
             'login': 'user_company_1',
             'email': 'somebody@somewhere.com',
             'groups_id': [
                 (6, 0, self.env.ref('base.group_partner_manager').ids)],
             'company_id': self.company_1.id,
             'company_ids': [(6, 0, self.company_1.ids)]})
        self.user_company_2 = self.env['res.users'].create(
            {'name': 'User company 2',
             'login': 'user_company_2',
             'email': 'somebody@somewhere.com',
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

    def test_create_company_1(self):
        partner = self.partner_model.sudo(self.user_company_1).create(
            {'name': 'Test from user company 1'})
        self.assertEqual(partner.company_id, self.company_1)

    def test_create_company_2(self):
        partner = self.partner_model.sudo(self.user_company_2).create(
            {'name': 'Test from user company 2'})
        self.assertEqual(partner.company_id, self.company_2)

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

    def test_switch_user_company(self):
        self.user_company_1.company_ids = (self.company_1 + self.company_2).ids
        self.user_company_1.company_id = self.company_2.id
        self.assertEqual(
            self.user_company_1.partner_id.company_id, self.company_2)

    def test_init_hook(self):
        """It should set company_ids even on deactivated partner."""
        deactivated_partner = self.env.ref('base.res_partner_20')
        self.assertEqual(deactivated_partner.company_ids.ids,
                         deactivated_partner.company_id.ids)
