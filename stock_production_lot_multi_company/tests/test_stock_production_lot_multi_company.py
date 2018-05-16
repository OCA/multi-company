# Copyright 2015 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestStockProductionLotMultiCompany(TransactionCase):

    def setUp(self):
        super(TestStockProductionLotMultiCompany, self).setUp()

        # models
        self.lot_model = self.env['stock.production.lot']
        self.picking_model = self.env['stock.picking']
        self.move_model = self.env['stock.move']
        self.company_model = self.env['res.company']
        self.user_model = self.env['res.users']
        self.product_model = self.env['product.product']

        # companies
        self.main_comp = self.env.ref('base.main_company')
        self.secondary_company = self.company_model.create({'name':
                                                            'SecondComp',
                                                            })

        # user groups
        self.lot_group = self.env.ref('stock.group_production_lot')
        self.stock_manager_group = self.env.ref('stock.group_stock_manager')
        self.group_multi_company = self.env.ref('base.group_multi_company')

        # creation of users by company
        self.second_user = self.user_model.create(
            {'name': 'Second company user',
             'login': 'secuser',
             'email': 'secuser@youcompany.com',
             'company_id': self.secondary_company.id,
             'company_ids': [(6, 0, [self.secondary_company.id])],
             'groups_id': [(6, 0, [self.stock_manager_group.id,
                                   self.lot_group.id,
                                   self.group_multi_company.id])],
             })
        self.main_user = self.user_model.create(
            {'name': 'Main company user',
             'login': 'mainuser',
             'email': 'mainuser@youcompany.com',
             'company_id': self.main_comp.id,
             'company_ids': [(6, 0, [self.main_comp.id,
                                     self.secondary_company.id])],
             'groups_id': [(6, 0, [self.stock_manager_group.id,
                                   self.lot_group.id,
                                   self.group_multi_company.id])],
             })
        self.multicomp_user = self.user_model.create(
            {'name': 'Multi company user',
             'login': 'multicompuser',
             'email': 'multicompuser@youcompany.com',
             'company_id': self.main_comp.id,
             'company_ids': [(6, 0, [self.main_comp.id,
                                     self.secondary_company.id])],
             'groups_id': [(6, 0, [self.stock_manager_group.id,
                                   self.lot_group.id,
                                   self.group_multi_company.id])],
             })

        self.unit_uom = self.env.ref('product.product_uom_unit')
        # product creation
        self.main_comp_product = self.product_model.create(
            {'name': 'Main company product',
             'default_code': '[MCP]',
             'company_id': self.main_comp.id,
             'tracking': 'serial',
             'uom_id': self.unit_uom.id})
        self.second_comp_product = self.product_model.create(
            {'name': 'Secondary company product',
             'default_code': '[SCP]',
             'company_id': self.secondary_company.id,
             'tracking': 'serial',
             'uom_id': self.unit_uom.id})

    def test_lot_main_creation(self):
        main_lot = self.lot_model.sudo(self.main_user.id).create(
            {'name': 'MAINLOT', 'product_id': self.main_comp_product.id})
        self.assertEqual(main_lot.company_id, self.main_comp,
                         'Incorrect company for the created lot in main '
                         'company user.')

    def test_lot_secondary_creation(self):
        secondary_lot = self.lot_model.sudo(self.second_user.id).create(
            {'name': 'SECONDARYLOT',
             'product_id': self.second_comp_product.id})
        self.assertEqual(secondary_lot.company_id, self.secondary_company,
                         'Incorrect company for the created lot in secondary '
                         'company user.')

    def test_lot_multicomp_creation(self):
        multicompuser_lot = self.lot_model.sudo(self.multicomp_user.id).create(
            {'name': 'MULTICOMPUSERLOT',
             'product_id': self.second_comp_product.id})
        self.assertEqual(multicompuser_lot.company_id, self.main_comp,
                         'Incorrect company for the created lot in '
                         'multicompany company user.')

    def test_error_lot_creation(self):
        with self.assertRaises(AccessError):
            self.lot_model.sudo(self.second_user.id).create(
                {'name': 'ERRORLOT',
                 'product_id': self.second_comp_product.id,
                 'company_id': self.main_comp.id})
