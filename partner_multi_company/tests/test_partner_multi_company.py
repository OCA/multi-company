# Copyright 2015 Oihane Crucelaegui
# Copyright 2015-2019 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common
from odoo.exceptions import AccessError


@common.at_install(False)
@common.post_install(True)
class TestPartnerMultiCompany(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPartnerMultiCompany, cls).setUpClass()
        # Avoid possible spam
        cls.partner_model = cls.env['res.partner'].with_context(
            mail_create_nosubscribe=True,
        )
        cls.company_1 = cls.env['res.company'].create(
            {'name': 'Test company 1'})
        cls.company_2 = cls.env['res.company'].create(
            {'name': 'Test company 2'})
        cls.partner_company_none = cls.partner_model.create(
            {'name': 'partner without company',
             'company_ids': False})
        cls.partner_company_1 = cls.partner_model.create(
            {'name': 'partner from company 1',
             'company_ids': [(6, 0, cls.company_1.ids)]})
        cls.partner_company_2 = cls.partner_model.create(
            {'name': 'partner from company 2',
             'company_ids': [(6, 0, cls.company_2.ids)]})
        cls.partner_company_both = cls.partner_model.create(
            {'name': 'partner for both companies',
             'company_ids': [(6, 0, (cls.company_1 + cls.company_2).ids)]})
        cls.user_company_1 = cls.env['res.users'].create({
            'name': 'User company 1',
            'login': 'user_company_1',
            'email': 'somebody@somewhere.com',
            'groups_id': [
                (4, cls.env.ref('base.group_partner_manager').id),
                (4, cls.env.ref('base.group_user').id),
            ],
            'company_id': cls.company_1.id,
            'company_ids': [(6, 0, cls.company_1.ids)],
        })
        cls.user_company_2 = cls.env['res.users'].create({
            'name': 'User company 2',
            'login': 'user_company_2',
            'email': 'somebody@somewhere.com',
            'groups_id': [
                (4, cls.env.ref('base.group_partner_manager').id),
                (4, cls.env.ref('base.group_user').id),
            ],
            'company_id': cls.company_2.id,
            'company_ids': [(6, 0, cls.company_2.ids)],
        })
        cls.partner_company_1 = cls.partner_company_1.sudo(cls.user_company_1)
        cls.partner_company_2 = cls.partner_company_2.sudo(cls.user_company_2)

    def test_create_partner(self):
        partner = self.env['res.partner'].create({'name': 'Test'})
        company = self.env['res.company']._company_default_get('res.partner')
        self.assertIn(company.id, partner.company_ids.ids)
        partner = self.env['res.partner'].create({
            'name': 'Test 2',
            'company_ids': [(4, self.company_1.id)],
        })
        self.assertEqual(
            partner.sudo(self.user_company_1).company_id.id,
            self.company_1.id,
        )
        partner = self.env['res.partner'].create({
            'name': 'Test 2',
            'company_ids': [(5, False)],
        })
        self.assertFalse(partner.company_id)

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
        partner = self.partner_model.sudo(self.user_company_1).create({
            'name': 'Test from user company 1',
            'company_ids': [(6, 0, self.company_1.ids)],
        })
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
        from ..hooks import uninstall_hook
        uninstall_hook(self.env.cr, None)
        rule = self.env.ref('base.res_partner_rule')
        domain = ("['|','|',"
                  "('company_id.child_ids','child_of',[user.company_id.id]),"
                  "('company_id','child_of',[user.company_id.id]),"
                  "('company_id','=',False)]")
        self.assertEqual(rule.domain_force, domain)
        self.assertFalse(rule.active)

    def test_switch_user_company(self):
        self.user_company_1.company_ids = (self.company_1 + self.company_2).ids
        self.user_company_1.company_id = self.company_2.id
        self.user_company_1 = self.user_company_1.sudo(self.user_company_2)
        self.assertEqual(
            self.user_company_1.partner_id.company_id,
            self.company_2,
        )

    def test_commercial_fields_implementation(self):
        """It should add company_ids to commercial fields."""
        self.assertIn(
            'company_ids',
            self.env['res.partner']._commercial_fields(),
        )

    def test_commercial_fields_result(self):
        """It should add company_ids to children partners."""
        partner = self.env['res.partner'].create({
            'name': 'Child test',
            'parent_id': self.partner_company_both.id,
        })
        self.assertEqual(
            partner.company_ids,
            self.partner_company_both.company_ids,
        )

    def test_avoid_updating_company_ids_in_global_partners(self):
        self.user_company_1.write({
            'company_ids': [(4, self.company_2.id)],
        })
        user_partner = self.user_company_1.partner_id
        user_partner.write({
            'company_id': False,
            'company_ids': [(5, False)],
        })
        self.user_company_1.write({
            'company_id': self.company_2.id,
        })
        self.assertEquals(user_partner.company_ids.ids, [])
