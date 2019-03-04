# -*- coding: utf-8 -*-
# Copyright 2019 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import Warning as UserError, ValidationError


class TestPricelist(TransactionCase):

    def setUp(self):
        super(TestPricelist, self).setUp()

        # configure multi company environment
        self.env['product.template'].search([]).write({'company_id': False})

        self.user = self.env.ref('base.user_demo')
        self.user.write({'groups_id': [
            (4, self.env.ref('sales_team.group_sale_manager').id)]})
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
        self.purchase_company = ref(
                'product_supplier_intercompany.res_company_purchase')

        # This is needed because global pricelist items aren't supported and
        # in version 10.0 a global item is created on pricelist creation
        self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', self.pricelist.id),
            ('applied_on', '=', '3_global')]).unlink()

        self.pricelist.is_intercompany_supplier = True
        self.supplier_info = self._get_supplier_info(self.product_template_1)

        self.not_intercompany_pricelist = ref(
                'product.list0')

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
        self.assertEqual(supplierinfo.price, price)

    def _add_item(self, record, price_surcharge, pricelist_id=None):
        '''
        All tests are done with list_price as base, cost and pricelist are not
        supported for now.
        This method does everything as formula but fixed and percent are tested
        as well.
        '''
        if not pricelist_id:
            pricelist_id = self.env.ref(
                'product_supplier_intercompany.pricelist_intercompany').id
        self.assertIn(record._name, ['product.product', 'product.template'])
        vals = {
            'pricelist_id': pricelist_id,
            'compute_price': 'formula',
            'base': 'list_price',
            'price_discount': 0.0,
            'price_surcharge': price_surcharge,
            }
        if record._name == 'product.product':
            vals.update({
                'applied_on': '0_product_variant',
                'product_id': record.id,
                'product_tmpl_id': record.product_tmpl_id.id,
                })
        else:
            vals.update({
                'applied_on': '1_product',
                'product_tmpl_id': record.id,
                })
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
        self._check_supplier_info_for(self.product_template_4, 760)
        self._check_supplier_info_for(self.product_product_4b, 765)
        self._check_supplier_info_for(self.product_template_1, 5)  # fixed
        self._check_supplier_info_for(self.product_product_2, 34.43)  # - 10%

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
        self._check_supplier_info_for(product, 480)

    def test_add_template_item(self):
        template = self.env.ref('product.product_product_2_product_template')
        self._add_item(template, 30)
        self._check_supplier_info_for(template, 68.25)

    def test_update_product_item(self):
        self.price_item_4b.price_surcharge = 40
        self._check_supplier_info_for(self.product_product_4b, 790)

    def test_change_product_item(self):
        self.price_item_4b.product_id = self.product_product_4c
        self._check_no_supplier_info_for(self.product_product_4b)
        self._check_supplier_info_for(self.product_product_4c, 815.4)

    def test_update_template_item(self):
        self.price_item_4.price_surcharge = 40
        self._check_supplier_info_for(self.product_template_4, 790)

    def test_remove_product_item(self):
        self.price_item_4b.unlink()
        self._check_no_supplier_info_for(self.product_product_4b)

    def test_remove_template_item(self):
        self.price_item_4.unlink()
        self._check_no_supplier_info_for(self.product_template_4)

    def test_raise_error_unlink_supplierinfo(self):
        with self.assertRaises(UserError):
            self.supplier_info.unlink()

    def test_raise_error_write_supplierinfo(self):
        with self.assertRaises(UserError):
            self.supplier_info.write({'product_code': 'TEST'})

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
            pricelist_id=self.not_intercompany_pricelist.id)
        self.assertEqual(
            nbr_supplier,
            self.env['product.supplierinfo'].sudo().search_count([]))

    def test_raise_error_forcing_recompute_with_not_intercompany(self):
        with self.assertRaises(UserError):
            product = self.env.ref('product.product_product_3')
            self._add_item(
                product, 30,
                pricelist_id=self.not_intercompany_pricelist.id)
            product._synchronise_supplier_info(
                pricelists=self.not_intercompany_pricelist)

    def test_add_product_item_no_intercompany_empty_todo(self):
        product = self.env.ref('product.product_product_3')
        item = self._add_item(
            product, 30,
            pricelist_id=self.not_intercompany_pricelist.id)
        todo = {}
        item._add_product_to_synchronize(todo)
        self.assertEqual(todo, {})

    def test_raise_error_required_company(self):
        with self.assertRaises(ValidationError):
            self.pricelist.company_id = False
