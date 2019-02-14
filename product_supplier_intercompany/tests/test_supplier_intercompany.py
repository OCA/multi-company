# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp.exceptions import Warning as UserError, ValidationError


class TestPricelist(TransactionCase):

    def setUp(self):
        super(TestPricelist, self).setUp()

        # configure multi company environment
        self.env['product.template'].search([]).write({'company_id': False})

        self.user = self.env.ref('base.user_demo')
        self.user.write({'groups_id': [
            (4, self.env.ref('base.group_sale_manager').id)]})
        self.env = self.env(user=self.user)
        ref = self.env.ref
        self.pricelist = ref(
            'product_supplier_intercompany.pricelist_intercompany')
        self.partner = ref('base.main_partner')

        self.product_template_4 = ref(
            'product.product_product_4_product_template')
        self.product_product_4b = ref('product.product_product_4b')
        self.product_product_4c = ref('product.product_product_4c')

        self.product_template_1 = ref(
            'product.product_product_1_product_template')
        self.product_product_2 = ref('product.product_product_2')

        self.price_item_4 = ref(
            'product_supplier_intercompany.pricelist_item_product_template_4')
        self.price_item_4b = ref(
            'product_supplier_intercompany.pricelist_item_product_product_4b')

        self.sale_company = ref('base.main_company')
        self.purchase_company = ref('stock.res_company_1')
        self.pricelist.is_intercompany_supplier = True
        self.supplier_info = self._get_supplier_info(self.product_template_1)

        self.not_intercompany_price_version = ref('product.ver0')

    def _get_supplier_info(self, record=None, sudo=True):
        domain = [
            ('name', '=', self.partner.id),
            ('intercompany_pricelist_id', '=', self.pricelist.id),
            ('company_id', '=', False),
            ]
        if record:
            self.assertIn(
                record._name, ['product.product', 'product.template'])
            if record._name == 'product.product':
                domain += [
                    ('product_tmpl_id', '=', record.product_tmpl_id.id),
                    ('product_id', '=', record.id),
                ]
            else:
                domain += [
                    ('product_tmpl_id', '=', record.id),
                    ('product_id', '=', False),
                ]
        supplierinfo_obj = self.env['product.supplierinfo']
        if sudo:
            supplierinfo_obj = supplierinfo_obj.sudo()
        return supplierinfo_obj.search(domain)

    def _check_no_supplier_info_for(self, record):
        supplierinfo = self._get_supplier_info(record)
        self.assertEqual(len(supplierinfo), 0)

    def _check_supplier_info_for(self, record, price):
        supplierinfo = self._get_supplier_info(record)
        self.assertEqual(len(supplierinfo), 1)
        self.assertEqual(len(supplierinfo.pricelist_ids), 1)
        self.assertEqual(supplierinfo.pricelist_ids.price, price)

    def _add_item(self, record, price, price_version_id=None):
        if not price_version_id:
            price_version_id = self.env.ref(
                'product_supplier_intercompany.pricelist_intercompany_v1').id
        self.assertIn(record._name, ['product.product', 'product.template'])
        ref = self.env.ref
        vals = {
            'price_version_id': price_version_id,
            'base': ref('product.list_price').id,
            'price_discount': -1,
            'price_surcharge': price,
            }
        if record._name == 'product.product':
            vals.update({
                'product_id': record.id,
                'product_tmpl_id': record.product_tmpl_id.id,
                })
        else:
            vals['product_tmpl_id'] = record.id
        return self.env['product.pricelist.item'].create(vals)

    def _switch_user_to_purchase_company(self):
        self.user.write({
            'company_id': self.purchase_company.id,
            'company_ids': [(6, 0, [
                self.purchase_company.id,
                self.sale_company.id,
                ])],
            })

    def test_set_pricelist_as_intercompany(self):
        supplierinfo = self._get_supplier_info()
        self.assertEqual(len(supplierinfo), 4)
        self._check_supplier_info_for(self.product_template_4, 10)
        self._check_supplier_info_for(self.product_product_4b, 15)
        self._check_supplier_info_for(self.product_template_1, 5)
        self._check_supplier_info_for(self.product_product_2, 20)

    def test_unset_pricelist_intercompany(self):
        self.pricelist.is_intercompany_supplier = False
        supplierinfo = self._get_supplier_info()
        self.assertEqual(len(supplierinfo), 0)

    def test_intercompany_access_rule(self):
        # Check that supplier this supplier info are not visible
        # with the current user "demo"
        supplierinfo = self._get_supplier_info(sudo=False)
        self.assertEqual(len(supplierinfo), 0)
        # Switch the company and check that the user can now see the supplier
        self._switch_user_to_purchase_company()
        supplierinfo = self._get_supplier_info(sudo=False)
        self.assertEqual(len(supplierinfo), 4)

    def test_add_product_item(self):
        product = self.env.ref('product.product_product_3')
        self._add_item(product, 30)
        self._check_supplier_info_for(product, 30)

    def test_add_template_item(self):
        template = self.env.ref('product.product_product_2_product_template')
        self._add_item(template, 30)
        self._check_supplier_info_for(template, 30)

    def test_update_product_item(self):
        self.price_item_4b.price_surcharge = 40
        self._check_supplier_info_for(self.product_product_4b, 40)

    def test_change_product_item(self):
        self.price_item_4b.product_id = self.product_product_4c
        self._check_no_supplier_info_for(self.product_product_4b)
        self._check_supplier_info_for(self.product_product_4c, 15)

    def test_update_template_item(self):
        self.price_item_4.price_surcharge = 40
        self._check_supplier_info_for(self.product_template_4, 40)

    def test_remove_product_item(self):
        self.price_item_4b.unlink()
        self._check_no_supplier_info_for(self.product_product_4b)

    def test_remove_template_item(self):
        self.price_item_4.unlink()
        self._check_no_supplier_info_for(self.product_template_4)

    def test_raise_error_unlink_supplierinfo(self):
        with self.assertRaises(UserError):
            self.supplier_info.unlink()

    def test_raise_error_unlink_supplierinfo_items(self):
        with self.assertRaises(UserError):
            self.supplier_info.pricelist_ids.unlink()

    def test_raise_error_write_supplierinfo(self):
        with self.assertRaises(UserError):
            self.supplier_info.write({'product_code': 'TEST'})

    def test_raise_error_write_supplierinfo_items(self):
        with self.assertRaises(UserError):
            self.supplier_info.pricelist_ids.write({'price': 100})

    def test_raise_error_create_supplierinfo(self):
        with self.assertRaises(UserError):
            self.env['product.supplierinfo'].sudo().create({
                'company_id': False,
                'name': self.partner.id,
                'product_tmpl_id': self.product_template_1.id,
                'intercompany_pricelist_id': self.pricelist.id,
                })

    def test_add_product_item_no_intercompany(self):
        product = self.env.ref('product.product_product_3')
        nbr_supplier = self.env['product.supplierinfo'].sudo().search_count([])
        self._add_item(
            product, 30,
            price_version_id=self.not_intercompany_price_version.id)
        self.assertEqual(
            nbr_supplier,
            self.env['product.supplierinfo'].sudo().search_count([]))

    def test_raise_error_forcing_recompute_with_not_intercompany(self):
        with self.assertRaises(UserError):
            product = self.env.ref('product.product_product_3')
            self._add_item(
                product, 30,
                price_version_id=self.not_intercompany_price_version.id)
            product._synchronise_supplier_info(
                pricelists=self.not_intercompany_price_version.pricelist_id)

    def test_add_product_item_no_intercompany_empty_todo(self):
        product = self.env.ref('product.product_product_3')
        item = self._add_item(
            product, 30,
            price_version_id=self.not_intercompany_price_version.id)
        todo = {}
        item._add_product_to_synchronize(todo)
        self.assertEqual(todo, {})

    def test_raise_error_required_company(self):
        with self.assertRaises(ValidationError):
            self.pricelist.company_id = False
