# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


class TestPricelist(TransactionCase):

    def setUp(self):
        super(TestPricelist, self).setUp()
        self.pricelist = self.env.ref(
                'product_supplier_intercompany.pricelist_intercompany')
        self.item = self.env.ref(
                'product_supplier_intercompany.pricelistitem1')
        # will be needed in version 10 (if global still not supported)
        # self.env['product.pricelist.item'].search([
        #    ('pricelist_id', '=', self.pricelist_id.id),
        #    ('applied_on', '=', '3_global')]).unlink()

    def test_pricelist_set_unset_supplier(self):
        self.pricelist.set_as_intercompany_supplier()
        supplierinfo = self.env['product.supplierinfo'].search(
            ['|',
                ('product_tmpl_id', '=',
                    self.item.product_id.product_tmpl_id.id),
                ('product_id.id', '=', self.item.product_id.id)])
        print('RES', supplierinfo)
        self.pricelist.unset_as_intercompany_supplier()
        supplierinfo = self.env['product.supplierinfo'].search(
            ['|',
                ('product_tmpl_id', '=',
                    self.item.product_id.product_tmpl_id.id),
                ('product_id.id', '=', self.item.product_id.id)])
        print('RES', supplierinfo)

    def test_supplier_add_pricelistitem(self):
        self.pricelist.set_as_intercompany_supplier()
        new = self.env['product.pricelist.item'].create({
            'price_version_id': self.item.price_version_id.id,
            'product_id': self.env.ref('product.product_product_4b').id,
            })
        supplierinfo = self.env['product.supplierinfo'].search(
            ['|',
                ('product_tmpl_id', '=', new.product_id.product_tmpl_id.id),
                ('product_id.id', '=', new.product_id.id)])
        print('RES', supplierinfo)
