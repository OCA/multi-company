# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo.tests import common


class TestResCompanyAssignment(common.TransactionCase):

    def setUp(self):
        super(TestResCompanyAssignment, self).setUp()
        self.View = self.env['res.company.assignment']
        self.Model = self.env['res.company']
        self.views = self.View.search([])

    def test_equality_len(self):
        """ The record lengths should match between mirror and original. """
        len_views = len(self.views)
        len_records = len(self.Model.search([]))
        self.assertEqual(len_views, len_records)

    def test_equality_data(self):
        """ The record data should match between mirror and original. """
        view = self.views[0]
        record = self.Model.browse(view.id)
        self.assertEqual(view.name, record.name)
