# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestResPartner(TransactionCase):

    def with_context(self, *args, **kwargs):
        context = dict(args[0] if args else self.env.context, **kwargs)
        self.env = self.env(context=context)
        return self

    def setUp(self):
        super(TestResPartner, self).setUp()
        employees_group = self.env.ref('base.group_user')
        partner_manager_group = self.env.ref('base.group_partner_manager')
        self.company = self.env['res.company'].create({
            'name': 'Test company'
        })
        self.company_2 = self.env['res.company'].create({
            'name': 'Test company 2',
            'parent_id': self.company.id,
        })
        self.env.user.company_ids += self.company
        self.env.user.company_ids += self.company_2

        self.with_context(
            company_id=self.company.id, force_company=self.company.id)
        self.user = self.env['res.users'].sudo(self.env.user).with_context(
            no_reset_password=True).create(
            {'name': 'Test User',
             'login': 'test_user',
             'email': 'test@oca.com',
             'groups_id': [(6, 0, [employees_group.id,
                                   partner_manager_group.id])],
             'company_id': self.company.id,
             'company_ids': [(4, self.company.id)],
             })

    def test_constrains(self):
        """Check contrains methods"""

        partner_1 = self.env['res.partner'].sudo(self.user).create({
            'name': 'Test',
            'company_id': self.company.id,
            'is_company': True,
        })
        partner_2 = self.env['res.partner'].sudo(self.user).create({
            'name': 'Test',
            'company_id': self.company_2.id,
            'is_company': False,
        })
        partner_3 = self.env['res.partner'].sudo(self.user).create({
            'name': 'Test',
            'company_id': self.company_2.id,
            'is_company': False,
        })
        with self.assertRaises(ValidationError):
            partner_1.child_ids += partner_2
        with self.assertRaises(ValidationError):
            partner_2.parent_id = partner_1
        partner_1.company_id = self.company_2
        partner_2.parent_id = partner_1
        partner_3.parent_id = partner_2
        partner_2.parent_id = False
        self.assertEqual(partner_3.commercial_partner_id, partner_2)
