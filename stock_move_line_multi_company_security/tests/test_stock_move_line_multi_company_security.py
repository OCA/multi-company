# Copyright 2018 Tecnativa S.L. - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import AccessError
from odoo.tests import common


class TestStockMoveLineMultiCompany(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockMoveLineMultiCompany, cls).setUpClass()
        cls.company_obj = cls.env['res.company']
        cls.user_obj = cls.env['res.users']
        cls.picking_obj = cls.env['stock.picking']
        cls.picking_type_internal = cls.env.ref('stock.picking_type_internal')
        cls.picking_type_out = cls.env.ref('stock.picking_type_out')
        cls.warehouse_obj = cls.env['stock.warehouse']
        cls.stock_move_obj = cls.env['stock.move']
        cls.stock_user_group = cls.env.ref('stock.group_stock_user')
        cls.company_a = cls.company_obj.create({'name': 'Test Company A'})
        cls.company_b = cls.company_obj.create({'name': 'Test Company B'})
        cls.user_comp_a = cls.user_obj.create({
            'name': 'Test User A',
            'login': 'test_user_a',
            'email': 'test_user_a@test_a.com',
            'company_id': cls.company_a.id,
            'company_ids': [(6, 0, [cls.company_a.id])],
            'groups_id': [(6, 0, [cls.stock_user_group.id])],
        })
        cls.user_comp_b = cls.user_obj.create({
            'name': 'Test User B',
            'login': 'test_user_b',
            'email': 'test_user_b@test_b.com',
            'company_id': cls.company_b.id,
            'company_ids': [(6, 0, [cls.company_b.id])],
            'groups_id': [(6, 0, [cls.stock_user_group.id])],
        })
        cls.warehouse_a = cls.warehouse_obj.create({
            'name': 'Test Warehouse A',
            'code': 'TSTA',
            'company_id': cls.company_a.id,
        })
        cls.warehouse_b = cls.warehouse_obj.create({
            'name': 'Test Warehouse B',
            'code': 'TSTB',
            'company_id': cls.company_b.id,
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test product',
        })
        cls.picking_B_customer = cls.env['stock.picking'].create({
            'location_id': cls.warehouse_b.lot_stock_id.id,
            'location_dest_id': cls.customer.property_stock_customer.id,
            'partner_id': cls.customer.id,
            'picking_type_id': cls.picking_type_out.id,
        })
        cls.stock_move_obj.create({
            'name': cls.product.name,
            'product_id': cls.product.id,
            'product_uom_qty': 99,
            'product_uom': cls.product.uom_id.id,
            'picking_id': cls.picking_B_customer.id,
            'location_id': cls.picking_B_customer.location_id.id,
            'location_dest_id': cls.picking_B_customer.location_dest_id.id,
        })
        cls.picking_B_customer.action_confirm()
        cls.picking_B_customer.move_lines.quantity_done = 10
        cls.picking_B_customer.button_validate()
        cls.move_line_b = cls.picking_B_customer.move_line_ids

    def test_stock_move_line_security(self):
        """ User A tries to read move line from company B"""
        with self.assertRaises(AccessError):
            self.move_line_b.sudo(self.user_comp_a).qty_done
