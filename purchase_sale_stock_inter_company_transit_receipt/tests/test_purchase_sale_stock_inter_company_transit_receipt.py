# Copyright 2026 Akretion
# @author Guillaume MASSON <guillaume.masson@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form

from odoo.addons.purchase_sale_stock_inter_company.tests.common import (
    TestPurchaseSaleStockInterCompanyCommon,
)


class TestPurchaseSaleStockInterCompanyTransitReceipt(
    TestPurchaseSaleStockInterCompanyCommon
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a.sync_picking = True
        cls.company_a.sync_picking_transit_receipt = True

    def _ship(self, sale, quantity, backorder=True):
        delivery = sale.picking_ids.filtered(lambda p: p.state != "done")
        delivery.move_ids.quantity = quantity
        delivery.move_ids.picked = True
        res = delivery.with_user(self.user_company_b).button_validate()
        if isinstance(res, dict):
            wizard = Form.from_action(self.env, res).save()
            if backorder:
                wizard.process()
            else:
                wizard.process_cancel_backorder()

    def _ship_serials(self, sale, serials):
        delivery = sale.picking_ids
        move = delivery.move_ids
        move_line_vals = move._prepare_move_line_vals()
        move.move_line_ids = [Command.clear()] + [
            Command.create(dict(move_line_vals, quantity=1, lot_id=serial.id))
            for serial in serials
        ]
        delivery.with_user(self.user_company_b).button_validate()

    def _physical_receipts(self, purchase):
        return purchase.picking_ids.move_ids.move_dest_ids.picking_id

    def test_group_company_purchase_gets_transit_receipt_type(self):
        purchase = self._create_purchase_order(self.partner_company_b)
        self.assertEqual(purchase.picking_type_id, self.warehouse_a.transit_in_type_id)

    def test_other_supplier_purchase_keeps_receipt_type(self):
        supplier = self.env["res.partner"].create({"name": "Supplier"})
        purchase = self._create_purchase_order(supplier)
        self.assertEqual(purchase.picking_type_id, self.warehouse_a.in_type_id)

    def test_sync_picking_without_transit_receipt_keeps_receipt_type(self):
        self.company_a.sync_picking_transit_receipt = False
        purchase = self._create_purchase_order(self.partner_company_b)
        self.assertEqual(purchase.picking_type_id, self.warehouse_a.in_type_id)

    def test_transit_receipt_requires_sync_picking(self):
        self.company_a.sync_picking = False
        purchase = self._create_purchase_order(self.partner_company_b)
        self.assertEqual(purchase.picking_type_id, self.warehouse_a.in_type_id)

    def test_seller_without_sale_from_purchase_keeps_receipt_type(self):
        self.company_b.so_from_po = False
        purchase = self._create_purchase_order(self.partner_company_b)
        self.assertEqual(purchase.picking_type_id, self.warehouse_a.in_type_id)

    def test_seller_delivery_validates_transit_receipt(self):
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)
        self._ship(sale, 3)
        transit_receipt = purchase.picking_ids
        self.assertEqual(transit_receipt.state, "done")
        self.assertEqual(
            transit_receipt.location_dest_id,
            self.warehouse_a.transit_in_type_id.default_location_dest_id,
        )
        self.assertEqual(transit_receipt.move_ids.quantity, 3)
        physical_receipt = self._physical_receipts(purchase)
        self.assertEqual(physical_receipt.picking_type_id, self.warehouse_a.in_type_id)
        self.assertEqual(physical_receipt.state, "assigned")
        self.assertEqual(physical_receipt.move_ids.product_uom_qty, 3)
        self.assertEqual(purchase.order_line.qty_received, 0)

    def test_physical_receipt_sets_received_quantity(self):
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)
        self._ship(sale, 3)
        physical_receipt = self._physical_receipts(purchase)
        physical_receipt.move_ids.picked = True
        physical_receipt.button_validate()
        self.assertEqual(physical_receipt.state, "done")
        self.assertEqual(purchase.order_line.qty_received, 3)

    def test_partial_delivery_backorders_transit_receipt(self):
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)
        self._ship(sale, 1)
        transit_receipt = purchase.picking_ids.filtered(lambda p: p.state == "done")
        self.assertEqual(transit_receipt.move_ids.quantity, 1)
        backorder = purchase.picking_ids - transit_receipt
        self.assertEqual(backorder.backorder_id, transit_receipt)
        self.assertEqual(backorder.state, "waiting")
        self.assertEqual(backorder.move_ids.product_uom_qty, 2)
        self.assertEqual(self._physical_receipts(purchase).move_ids.product_uom_qty, 1)
        self._ship(sale, 2)
        self.assertEqual(backorder.state, "done")
        self.assertEqual(backorder.move_ids.quantity, 2)
        self.assertEqual(
            sum(self._physical_receipts(purchase).move_ids.mapped("product_uom_qty")),
            3,
        )
        self.assertEqual(purchase.order_line.qty_received, 0)

    def test_delivery_without_backorder_cancels_transit_receipt_rest(self):
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)
        self._ship(sale, 1, backorder=False)
        self.assertEqual(purchase.picking_ids.state, "done")
        self.assertEqual(purchase.picking_ids.move_ids.quantity, 1)
        self.assertEqual(self._physical_receipts(purchase).move_ids.product_uom_qty, 1)

    def test_serials_carried_to_transit_and_physical_receipts(self):
        purchase = self._create_purchase_order(
            self.partner_company_b, self.stockable_product_serial
        )
        sale = self._approve_po(purchase)
        serials = self.serial_1 | self.serial_2 | self.serial_3
        self._ship_serials(sale, serials)
        transit_receipt = purchase.picking_ids
        self.assertEqual(transit_receipt.state, "done")
        self.assertEqual(transit_receipt.move_line_ids.lot_id, serials)
        physical_receipt = self._physical_receipts(purchase)
        self.assertEqual(physical_receipt.state, "assigned")
        self.assertEqual(physical_receipt.move_line_ids.lot_id, serials)

    def test_sync_never_touches_physical_receipts(self):
        self.warehouse_a.reception_steps = "two_steps"
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)
        self._ship(sale, 1)
        self._ship(sale, 2)
        self.assertEqual(set(purchase.picking_ids.mapped("state")), {"done"})
        physical_receipts = self._physical_receipts(purchase)
        self.assertEqual(physical_receipts.picking_type_id, self.warehouse_a.in_type_id)
        self.assertEqual(set(physical_receipts.mapped("state")), {"assigned"})
        self.assertFalse(physical_receipts & purchase.picking_ids)
        self.assertFalse(physical_receipts.intercompany_picking_id)

    def test_serials_carried_from_inter_company_location(self):
        self.company_a._set_per_company_inter_company_locations(
            self.env.ref("stock.stock_location_inter_company")
        )
        purchase = self._create_purchase_order(
            self.partner_company_b, self.stockable_product_serial
        )
        sale = self._approve_po(purchase)
        serials = self.serial_1 | self.serial_2 | self.serial_3
        self._ship_serials(sale, serials)
        transit_receipt = purchase.picking_ids
        self.assertEqual(transit_receipt.location_id.usage, "transit")
        self.assertEqual(transit_receipt.state, "done")
        self.assertEqual(transit_receipt.move_line_ids.lot_id, serials)
        physical_receipt = self._physical_receipts(purchase)
        self.assertEqual(physical_receipt.state, "assigned")
        self.assertEqual(physical_receipt.move_line_ids.lot_id, serials)
