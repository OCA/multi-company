# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests import TransactionCase


class TestMulticompanyProperty(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company_1 = self.create_company('company 1')
        self.company_2 = self.create_company('company 2')
        self.partner = self.env['res.partner'].create({
            'name': 'Partner',
            'company_id': False,
        })

    def create_company(self, name):
        return self.env['res.company'].create({
            'name': name
        })

    def test_partner(self):
        self.assertTrue(self.partner.property_ids)
