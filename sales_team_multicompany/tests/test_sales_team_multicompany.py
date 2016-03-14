# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase
from openerp.exceptions import AccessError


class TestSalesTeamMultiCompany(TransactionCase):
    def test_create_sale_order_with_sale_team(self):
        res_users1 = self.env.ref('sales_team_multicompany.res_users1')
        res_users2 = self.env.ref('sales_team_multicompany.res_users2')
        res_partner1 = self.env.ref('sales_team_multicompany.res_partner1')
        res_partner2 = self.env.ref('sales_team_multicompany.res_partner2')
        crm_team2 = self.env.ref(
            'sales_team_multicompany.crm_team2')
        crm_team_both = self.env.ref(
            'sales_team_multicompany.crm_team_both')
        # All of this should be allowed
        self.env['sale.order'].create(
            {'name': 'TEST 1',
             'partner_id': res_partner2.id,
             'team_id': (crm_team2.sudo(res_users2.id)
                         .read()[0]['id'])})
        self.env['sale.order'].create(
            {'name': 'TEST 2',
             'partner_id': res_partner1.id,
             'team_id': (crm_team_both.sudo(res_users1.id)
                         .read()[0]['id'])})
        # And this one not
        with self.assertRaises(AccessError):
            self.env['sale.order'].create(
                {'name': 'TEST',
                 'partner_id': res_partner1.id,
                 'team_id': (crm_team2.sudo(res_users1.id)
                             .read()[0]['id'])})
