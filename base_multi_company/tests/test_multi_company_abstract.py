# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import exceptions, fields, models
from odoo.tests import common


class MultiCompanyAbstractTester(models.TransientModel):
    _name = 'multi.company.abstract.tester'
    _inherit = 'multi.company.abstract'

    name = fields.Char()


class TestMultiCompanyAbstract(common.SavepointCase):

    @classmethod
    def _init_test_model(cls, model_cls):
        """ It builds a model from model_cls in order to test abstract models.
        Note that this does not actually create a table in the database, so
        there may be some unidentified edge cases.
        Args:
            model_cls (odoo.models.BaseModel): Class of model to initialize
        Returns:
            model_cls: Instance
        """
        registry = cls.env.registry
        cr = cls.env.cr
        inst = model_cls._build_model(registry, cr)
        model = cls.env[model_cls._name].with_context(todo=[])
        model._prepare_setup()
        model._setup_base(partial=False)
        model._setup_fields(partial=False)
        model._setup_complete()
        model._auto_init()
        model.init()
        model._auto_end()
        cls.test_model_record = cls.env['ir.model'].search([
            ('name', '=', model._name),
        ])
        return inst

    @classmethod
    def setUpClass(cls):
        super(TestMultiCompanyAbstract, cls).setUpClass()
        cls.env.registry.enter_test_mode()
        cls._init_test_model(MultiCompanyAbstractTester)
        cls.test_model = cls.env[MultiCompanyAbstractTester._name]

    @classmethod
    def tearDownClass(cls):
        cls.env.registry.leave_test_mode()
        super(TestMultiCompanyAbstract, cls).tearDownClass()

    def setUp(self):
        super(TestMultiCompanyAbstract, self).setUp()
        self.Model = self.env['multi.company.abstract.tester']
        self.record = self.Model.create({
            'name': 'test',
            'active': True,
        })
        Companies = self.env['res.company']
        self.company_1 = Companies._company_default_get()
        self.company_2 = Companies.create({
            'name': 'Test Co 2',
            'account_no': '123456'
        })

    def add_company(self, company):
        """ Add company to the test record. """
        self.record.company_ids = [4, company.id]

    def switch_user_company(self, user, company):
        """ Add a company to the user's allowed & set to current. """
        user.write({
            'company_ids': [(6, 0, (company + user.company_ids).ids)],
            'company_id': company.id,
        })

    def test_default_company_ids(self):
        """ It should set company_ids to the default company. """
        self.assertEqual(
            self.record.company_ids.ids,
            self.company_1.ids,
        )

    def test_compute_company_id(self):
        """ It should set company_id to the top of the company_ids stack. """
        self.add_company(self.company_2)
        self.assertEqual(
            self.record.company_id.id,
            self.record.company_ids[0].id,
        )

    def test_inverse_company_id(self):
        """ It should add the company using company_id. """
        self.record.company_id = self.company_2
        self.assertIn(self.company_2.id, self.record.company_ids.ids)

    def test_search_company_id(self):
        """ It should return correct record by searching company_id. """
        self.add_company(self.company_2)
        record = self.env['multi.company.abstract.tester'].search([
            ('company_id.account_no', '=', self.company_2.account_no),
            ('id', '=', self.record.id),
        ])
        self.assertEqual(record, self.record)
        record = self.env['multi.company.abstract.tester'].search([
            ('company_id', '=', self.company_1.id),
            ('id', '=', self.record.id),
        ])
        self.assertEqual(record, self.record)
        record = self.env['multi.company.abstract.tester'].search([
            ('company_ids', 'child_of', self.company_1.id),
            ('id', '=', self.record.id),
        ])
        self.assertEqual(record, self.record)
        record = self.env['multi.company.abstract.tester'].search([
            ('company_ids', 'parent_of', self.company_1.id),
            ('id', '=', self.record.id),
        ])
        self.assertEqual(record, self.record)

    def test_compute_company_id2(self):
        """
        Test the computation of company_id for a multi_company_abstract.
        We have to ensure that the priority of the computed company_id field
        is given on the current company of the current user.
        And not a random company into allowed companies (company_ids of the
        target model).
        Because most of access rights are based on the current company of the
        current user and not on allowed companies (company_ids).
        :return: bool
        """
        user_obj = self.env['res.users']
        company_obj = self.env['res.company']
        tester_obj = self.env['multi.company.abstract.tester']
        company1 = self.env.ref("base.main_company")
        # Create companies
        company2 = company_obj.create({
            'name': 'High salaries',
        })
        company3 = company_obj.create({
            'name': 'High salaries, twice more!',
        })
        company4 = company_obj.create({
            'name': 'No salaries',
        })
        companies = company1
        companies |= company2
        companies |= company3
        # Create a "normal" user (not the admin)
        user = user_obj.create({
            'name': 'Best employee',
            'login': 'best-emplyee@example.com',
            'company_id': company1.id,
            'company_ids': [(6, False, companies.ids)],
        })
        tester = tester_obj.create({
            'name': 'My tester',
            'company_ids': [(6, False, companies.ids)],
        })
        tester = tester.sudo(user)
        # Current company_id should be updated with current company of the user
        for company in user.company_ids:
            user.write({
                'company_id': company.id,
            })
            # Force recompute
            tester.invalidate_cache()
            # Ensure that the current user is on the right company
            self.assertEqual(user.company_id.id, company.id)
            self.assertEqual(tester.company_id.id, company.id)
            # So can read company fields without Access error
            self.assertTrue(bool(tester.company_id.name))
        # Switch to a company not in tester.company_ids
        user.write({
            'company_ids': [(4, company4.id, False)],
            'company_id': company4.id,
        })
        # Force recompute
        tester.invalidate_cache()
        self.assertNotEqual(user.company_id.id, tester.company_ids.ids)
        with self.assertRaises(exceptions.AccessError):
            # The company is not allowed (because not the current company
            # of the user) so we should have an exception in this case
            self.assertTrue(bool(tester.company_id.name))
        return True
