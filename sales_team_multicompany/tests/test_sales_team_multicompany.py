# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase
from openerp.exceptions import AccessError


class TestSalesTeamMultiCompany(TransactionCase):
    def setUp(self):
        super(TestSalesTeamMultiCompany, self).setUp()

        # models
        self.company_model = self.env['res.company']
        self.user_model = self.env['res.users']
        self.partner_model = self.env['res.partner']

        # companies
        self.main_company = self.env.ref('base.main_company')
        self.currency_usd = self.env.ref('base.USD')
        self.secondary_company = self.company_model.create(
            {'name': 'SecondCompany',
             'currency_id': self.currency_usd.id,
             'rml_header': self.main_company.rml_header,
             'rml_header2': self.main_company.rml_header2,
             'rml_header3': self.main_company.rml_header3,
             'rml_paper_format': self.main_company.rml_paper_format,
             })

        # user groups
        self.group_user = self.env.ref('base.group_user')
        self.group_sale_salesman = self.env.ref('base.group_sale_salesman')

        # users
        self.user_demo1 = self.env.ref('base.user_demo')
        self.user_demo2 = self.user_model.create(
            {'name': 'User demo 2',
             'login': 'demo2',
             'password': 'demo2',
             'company_id': self.secondary_company.id,
             'company_ids': [(6, 0, [self.secondary_company.id])],
             'groups_id': [(6, 0, [self.group_user.id,
                                   self.group_sale_salesman.id])],
             })

        # partners
        self.partner1 = self.env.ref('base.res_partner_1')
        self.partner2 = self.env.ref('base.res_partner_2')

        # sales teams
        self.team_sales_department = self.env.ref(
            'sales_team.team_sales_department')
        self.crm_team_1 = self.env.ref('sales_team.crm_team_1')

    def test_create_sale_order_with_sale_team(self):
        # All of this should be allowed
        self.env['sale.order'].create(
            {'name': 'TEST 1',
             'partner_id': self.partner2.id,
             'team_id': (self.crm_team_1.sudo(self.user_demo1.id)
                         .read()[0]['id']),
             })
        self.env['sale.order'].create(
            {'name': 'TEST 2',
             'partner_id': self.partner1.id,
             'team_id': (self.team_sales_department.sudo(self.user_demo2.id)
                         .read()[0]['id']),
             })
        # And this one not
        with self.assertRaises(AccessError):
            self.env['sale.order'].create(
                {'name': 'TEST',
                 'partner_id': self.partner1.id,
                 'team_id': (self.crm_team_1.sudo(self.user_demo2.id)
                             .read()[0]['id']),
                 })
