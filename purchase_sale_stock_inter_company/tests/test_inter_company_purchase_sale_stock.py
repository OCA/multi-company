# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError

from odoo.addons.purchase_sale_inter_company.tests import (
    test_inter_company_purchase_sale as test_icps,
)

TestPurchaseSaleInterCompany = test_icps.TestPurchaseSaleInterCompany


class TestPurchaseSaleStockInterCompany(TestPurchaseSaleInterCompany):
    @classmethod
    def _configure_user(cls, user):
        res = super()._configure_user(user)
        # Add stock user group to the user
        # to prevent access errors during tests
        # When `stock_picking_batch` is installed,
        # the model stock.picking.batch
        # has access rights that restrict access to the group_stock_user
        user.groups_id |= cls.env.ref("stock.group_stock_user")
        return res

    @classmethod
    def _create_warehouse(cls, code, company):
        address = cls.env["res.partner"].create({"name": f"{code} address"})
        return cls.env["stock.warehouse"].create(
            {
                "name": f"Warehouse {code}",
                "code": code,
                "partner_id": address.id,
                "company_id": company.id,
            }
        )

    @classmethod
    def _create_serial_and_quant(cls, product, name, company, quant=True):
        lot = cls.lot_obj.create(
            {"product_id": product.id, "name": name, "company_id": company.id}
        )
        if quant:
            cls.quant_obj.create(
                {
                    "product_id": product.id,
                    "location_id": cls.warehouse_c.lot_stock_id.id,
                    "quantity": 1,
                    "lot_id": lot.id,
                }
            )
        return lot

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lot_obj = cls.env["stock.lot"]
        cls.quant_obj = cls.env["stock.quant"]
        # Configure 2 Warehouse per company
        cls.warehouse_a = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_a.id)]
        )
        cls.warehouse_b = cls._create_warehouse("CA-WB", cls.company_a)

        cls.warehouse_c = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_b.id)]
        )
        cls.warehouse_d = cls._create_warehouse("CB-WD", cls.company_b)
        cls.company_b.warehouse_id = cls.warehouse_c
        cls.consumable_product = cls.env["product.product"].create(
            {
                "name": "Consumable Product",
                "type": "consu",
                "is_storable": False,
                "categ_id": cls.env.ref("product.product_category_all").id,
                "qty_available": 100,
            }
        )
        cls.stockable_product_serial = cls.env["product.product"].create(
            {
                "name": "Stockable Product Tracked by Serial",
                "type": "consu",
                "is_storable": True,
                "tracking": "serial",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )
        # Add quants for product tracked by serial to supplier
        cls.serial_1 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "111", cls.env["res.company"]
        )
        cls.serial_2 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "222", cls.company_b
        )
        cls.serial_3 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "333", cls.company_b
        )
        cls.serial_4 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "444", cls.company_b
        )
        cls.serial_5 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "555", cls.company_b
        )

    def test_deliver_to_warehouse_a(self):
        self.purchase_company_a.picking_type_id = self.warehouse_a.in_type_id
        sale = self._approve_po()
        self.assertEqual(self.warehouse_a.partner_id, sale.partner_shipping_id)

    def test_deliver_to_warehouse_b(self):
        self.purchase_company_a.picking_type_id = self.warehouse_b.in_type_id
        sale = self._approve_po()
        self.assertEqual(self.warehouse_b.partner_id, sale.partner_shipping_id)

    def test_send_from_warehouse_c(self):
        self.company_b.warehouse_id = self.warehouse_c
        sale = self._approve_po()
        self.assertEqual(sale.warehouse_id, self.warehouse_c)

    def test_send_from_warehouse_d(self):
        self.company_b.warehouse_id = self.warehouse_d
        sale = self._approve_po()
        self.assertEqual(sale.warehouse_id, self.warehouse_d)

    def test_purchase_sale_stock_inter_company(self):
        self.purchase_company_a.notes = "Test note"
        sale = self._approve_po()
        self.assertEqual(
            sale.partner_shipping_id,
            self.purchase_company_a.picking_type_id.warehouse_id.partner_id,
        )
        self.assertEqual(sale.warehouse_id, self.warehouse_c)

    def test_sync_intercompany_picking_qty_with_backorder(self):
        self.product.type = "consu"
        self.company_a.sync_picking = True
        self.partner_company_b.company_id = False
        purchase = self.purchase_company_a
        sale = self._approve_po()
        sale_picking = sale.picking_ids[0]
        sale_picking.with_company(sale_picking.company_id).action_confirm()
        sale_picking.move_ids.quantity = 1.0
        sale_picking.move_ids.picked = True
        res_dict = sale_picking.with_company(sale_picking.company_id).button_validate()
        if isinstance(res_dict, dict) and "context" in res_dict:
            wizard = (
                self.env["stock.backorder.confirmation"]
                .with_context(**res_dict.get("context"))
                .create({})
            )
            wizard.process()
        sale_picking2 = sale.picking_ids.filtered(lambda p: p.state != "done")
        self.assertEqual(purchase.picking_ids[0].move_line_ids.quantity, 1)
        self.assertEqual(purchase.picking_ids[1].move_line_ids.quantity, 2)
        self.assertEqual(purchase.order_line.qty_received, 1)
        sale_picking2.move_ids.quantity = 2.0
        sale_picking2.with_company(sale_picking2.company_id).action_confirm()
        sale_picking2.with_company(sale_picking2.company_id).button_validate()
        self.assertEqual(purchase.picking_ids[0].move_line_ids.quantity, 1)
        self.assertEqual(purchase.picking_ids[1].move_line_ids.quantity, 2)
        self.assertEqual(purchase.order_line.qty_received, 3)

    def test_purchase_sale_with_two_products_no_backorder(self):
        self.product.type = "consu"
        self.partner_company_b.company_id = False
        self.product2 = self.env["product.product"].create(
            {"name": "Product 2", "type": "consu", "is_storable": True}
        )
        self.purchase_company_a.write(
            {
                "order_line": [
                    Command.create({"product_id": self.product2.id, "product_qty": 1}),
                ]
            }
        )
        sale = self._approve_po()
        sale_picking = sale.picking_ids
        self.assertEqual(len(sale.picking_ids), 1)
        sale_picking.with_company(sale_picking.company_id).action_confirm()
        for move in sale_picking.move_ids:
            move.quantity = move.product_uom_qty
        sale_picking.with_company(sale_picking.company_id).button_validate()
        self.assertEqual(len(self.purchase_company_a.picking_ids), 1)
        self.assertEqual(len(self.purchase_company_a.picking_ids.move_line_ids), 2)

    def test_sync_picking(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)

        self.assertTrue(purchase.picking_ids)
        self.assertTrue(sale.picking_ids)

        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        # check po_picking state
        self.assertEqual(po_picking_id.state, "waiting")

        # validate the SO picking
        so_picking_id.move_ids.quantity = 2

        self.assertNotEqual(po_picking_id, so_picking_id)
        self.assertNotEqual(
            po_picking_id.move_ids.quantity,
            so_picking_id.move_ids.quantity,
        )
        self.assertEqual(
            po_picking_id.move_ids.product_qty,
            so_picking_id.move_ids.product_qty,
        )
        wizard_data = so_picking_id.with_user(self.user_company_b).button_validate()
        wizard = (
            self.env["stock.backorder.confirmation"]
            .with_context(**wizard_data.get("context"))
            .create({})
        )
        wizard.process()

        # Quantities should have been synced
        self.assertNotEqual(po_picking_id, so_picking_id)
        self.assertEqual(
            po_picking_id.move_ids.quantity,
            so_picking_id.move_ids.quantity,
        )

        # Check picking state
        self.assertEqual(po_picking_id.state, so_picking_id.state)

        # A backorder should have been made for both
        self.assertTrue(len(sale.picking_ids) > 1)
        self.assertEqual(len(purchase.picking_ids), len(sale.picking_ids))

    def test_confirm_several_picking(self):
        """
        Ensure that confirming several picking is not broken
        """
        purchase_1 = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase_2 = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale_1 = self._approve_po(purchase_1)
        sale_2 = self._approve_po(purchase_2)
        pickings = sale_1.picking_ids | sale_2.picking_ids
        for move in pickings.move_ids:
            move.quantity = move.product_uom_qty
        pickings.button_validate()
        self.assertEqual(pickings.mapped("state"), ["done", "done"])

    def test_sync_picking_no_backorder(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)

        self.assertTrue(purchase.picking_ids)
        self.assertTrue(sale.picking_ids)

        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        # check po_picking state
        self.assertEqual(po_picking_id.state, "waiting")

        # validate the SO picking
        so_picking_id.move_ids.quantity = 2

        self.assertNotEqual(po_picking_id, so_picking_id)
        self.assertNotEqual(
            po_picking_id.move_ids.quantity,
            so_picking_id.move_ids.quantity,
        )
        self.assertEqual(
            po_picking_id.move_ids.product_qty,
            so_picking_id.move_ids.product_qty,
        )

        # No backorder
        wizard_data = so_picking_id.with_user(self.user_company_b).button_validate()
        wizard = (
            self.env["stock.backorder.confirmation"]
            .with_context(**wizard_data.get("context"))
            .create({})
        )
        wizard.with_user(self.user_company_b).process_cancel_backorder()
        self.assertEqual(so_picking_id.state, "done")
        self.assertEqual(po_picking_id.state, "done")

        # Quantity done should be the same on both sides, per product
        self.assertNotEqual(po_picking_id, so_picking_id)
        for product in so_picking_id.move_ids.mapped("product_id"):
            self.assertEqual(
                sum(
                    so_picking_id.move_ids.filtered(
                        lambda line, product=product: line.product_id == product
                    ).mapped("quantity")
                ),
                sum(
                    po_picking_id.move_ids.filtered(
                        lambda line, product=product: line.product_id == product
                    ).mapped("quantity")
                ),
            )

        # No backorder should have been made for both
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(len(purchase.picking_ids), len(sale.picking_ids))

    def test_sync_picking_lot(self):
        """
        Test that the lot is synchronized on the moves
        by searching or creating a new lot in the company of destination
        """
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.stockable_product_serial
        )
        sale = self._approve_po(purchase)

        # validate the SO picking
        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        so_move = so_picking_id.move_ids
        so_move.move_line_ids = [
            Command.clear(),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_1.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_2.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_3.id,
                    "picking_id": so_picking_id.id,
                },
            ),
        ]
        so_picking_id.button_validate()

        so_lots = so_move.mapped("move_line_ids.lot_id")
        po_lots = po_picking_id.mapped("move_ids.move_line_ids.lot_id")
        self.assertEqual(
            len(so_lots),
            len(po_lots),
            msg="There aren't the same number of lots on both moves",
        )
        self.assertEqual(
            so_lots, po_lots, msg="The lots of the moves should be the same"
        )
        self.assertEqual(
            so_lots.mapped("name"),
            po_lots.mapped("name"),
            msg="The lots should have the same name in both moves",
        )
        self.assertFalse(so_lots.company_id, msg="Lots should not have a company.")
        # create a new lot in the picking done
        move_line_vals = so_move._prepare_move_line_vals()
        move_line_vals.update({"lot_id": self.serial_4.id, "quantity": 1})
        new_move_line = self.env["stock.move.line"].create(move_line_vals)
        self.assertIn(
            self.serial_4.name,
            po_picking_id.mapped("move_ids.move_line_ids.lot_id.name"),
        )
        # change the lot in the picking done
        new_move_line.lot_id = self.serial_5
        self.assertIn(
            self.serial_5.name,
            po_picking_id.mapped("move_ids.move_line_ids.lot_id.name"),
        )
        self.assertNotIn(
            self.serial_4.name,
            po_picking_id.mapped("move_ids.move_line_ids.lot_id.name"),
        )

    def test_sync_picking_lot_with_transit_location(self):
        """
        Test that the lot is synchronized on the moves
        when using inter-company transit locations
        company B: Sale picking from Stock to Transit Location
        company A: Purchase picking from Transit Location to Stock
        """
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        # Set inter-company locations on partners
        interco_location = self.env.ref("stock.stock_location_inter_company")
        self.partner_company_b.with_company(self.company_a).write(
            {
                "property_stock_customer": interco_location.id,
                "property_stock_supplier": interco_location.id,
            }
        )
        self.partner_company_a.with_company(self.company_b).write(
            {
                "property_stock_customer": interco_location.id,
                "property_stock_supplier": interco_location.id,
            }
        )

        purchase = self._create_purchase_order(
            self.partner_company_b, self.stockable_product_serial
        )
        sale = self._approve_po(purchase)

        # validate the SO picking
        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        so_move = so_picking_id.move_ids
        so_move.move_line_ids = [
            Command.clear(),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_1.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_2.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_3.id,
                    "picking_id": so_picking_id.id,
                },
            ),
        ]
        so_picking_id.button_validate()
        self.assertEqual(so_picking_id.location_id.usage, "internal")
        self.assertEqual(so_picking_id.location_dest_id.usage, "transit")
        self.assertEqual(po_picking_id.location_id.usage, "transit")
        self.assertEqual(po_picking_id.location_dest_id.usage, "internal")

        so_lots = so_move.mapped("move_line_ids.lot_id")
        po_lots = po_picking_id.mapped("move_ids.move_line_ids.lot_id")
        self.assertEqual(
            len(so_lots),
            len(po_lots),
            msg="There aren't the same number of lots on both moves",
        )
        self.assertEqual(
            so_lots, po_lots, msg="The lots of the moves should be the same"
        )
        self.assertEqual(
            so_lots.mapped("name"),
            po_lots.mapped("name"),
            msg="The lots should have the same name in both moves",
        )
        self.assertFalse(so_lots.company_id, msg="Lots should not have a company.")

    def test_sync_picking_same_product_multiple_lines(self):
        """
        Picking synchronization should work even when there
        are multiple lines of the same product in the PO/SO/picking
        """
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        self.company_b.sale_auto_validation = False

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.order_line += purchase.order_line.copy({"product_qty": 2})
        sale = self._approve_po(purchase)
        sale.action_confirm()

        # validate the SO picking
        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        # Set quantities done on the picking and validate
        for move in so_picking_id.move_ids:
            move.quantity = move.product_uom_qty
        so_picking_id.button_validate()

        self.assertEqual(
            po_picking_id.mapped("move_ids.quantity"),
            so_picking_id.mapped("move_ids.quantity"),
            msg="The quantities are not the same in both pickings.",
        )

    def test_block_manual_validation(self):
        """
        Test that the manual validation of the picking is blocked
        when the flag is set in the destination company
        """
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        self.company_a.block_po_manual_picking_validation = True
        self.company_b.block_po_manual_picking_validation = True
        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.button_confirm()
        po_picking_id = purchase.picking_ids
        # The picking should be in waiting state
        self.assertEqual(po_picking_id.state, "waiting")
        # The manual validation should be blocked
        with self.assertRaisesRegex(
            UserError, "Manual validation of the picking is not allowed"
        ):
            po_picking_id.with_user(self.user_company_a).button_validate()

    def test_notify_picking_problem(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        self.company_b.sale_auto_validation = False
        self.company_a.sync_picking_failure_action = "notify"
        self.company_b.sync_picking_failure_action = "notify"
        self.company_a.notify_user_id = self.user_company_a
        self.company_b.notify_user_id = self.user_company_b

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase_2 = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.order_line += purchase.order_line.copy({"product_qty": 2})
        sale = self._approve_po(purchase)
        sale.action_confirm()

        # validate the SO picking
        so_picking_id = sale.picking_ids

        # Link to a new purchase order so it can trigger
        # `PO does not exist or has no receipts` in _sync_receipt_with_delivery
        sale.auto_purchase_order_id = purchase_2

        # Set quantities done on the picking and validate
        for move in so_picking_id.move_ids:
            move.quantity = move.product_uom_qty
        so_picking_id.button_validate()

        # Test that picking has an activity now
        self.assertTrue(len(so_picking_id.activity_ids) > 0)
        activity_warning = self.env.ref("mail.mail_activity_data_warning")
        warning_activity = so_picking_id.activity_ids.filtered(
            lambda a: a.activity_type_id == activity_warning
        )
        self.assertEqual(len(warning_activity), 1)

        # Test the user assigned to the activity
        self.assertEqual(
            warning_activity.user_id, so_picking_id.company_id.notify_user_id
        )

    def test_raise_picking_problem(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        self.company_b.sale_auto_validation = False
        self.company_a.sync_picking_failure_action = "raise"
        self.company_b.sync_picking_failure_action = "raise"

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase_2 = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        purchase.order_line += purchase.order_line.copy({"product_qty": 2})
        sale = self._approve_po(purchase)
        sale.action_confirm()

        # validate the SO picking
        so_picking_id = sale.picking_ids

        # Link to a new purchase order so it can trigger
        # `PO does not exist or has no receipts` in _sync_receipt_with_delivery
        sale.auto_purchase_order_id = purchase_2

        # Set quantities done on the picking and validate
        for move in so_picking_id.move_ids:
            move.quantity = move.product_uom_qty
        with self.assertRaisesRegex(UserError, "There's no corresponding line in PO"):
            so_picking_id.button_validate()

    def test_sync_picking_multi_step(self):
        self.company_a.sync_picking = True
        self.warehouse_a.reception_steps = "two_steps"
        self.company_b.sync_picking = True
        self.warehouse_c.delivery_steps = "pick_ship"

        purchase = self._create_purchase_order(
            self.partner_company_b, self.consumable_product
        )
        sale = self._approve_po(purchase)

        self.assertEqual(len(purchase.picking_ids), 1)
        # Only a single picking is created for the sale.
        # When this picking is validated, two pickings should be created:
        # one for the backorder and one for the delivery.
        self.assertEqual(len(sale.picking_ids), 1)
        # validate the SO internal picking
        so_internal_pick = sale.picking_ids

        so_internal_pick.move_ids.quantity = 2
        so_internal_pick.move_ids.picked = True
        wizard_data = so_internal_pick.with_user(self.user_company_b).button_validate()
        wizard = (
            self.env["stock.backorder.confirmation"]
            .with_context(**wizard_data.get("context"))
            .create({})
        )
        wizard.process()
        po_picking = purchase.picking_ids
        # check po_picking state
        self.assertEqual(po_picking.state, "waiting")

        # validate the SO picking
        so_picking = sale.picking_ids.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        )
        so_picking.move_ids.quantity = 2
        so_picking.move_ids.picked = True
        self.assertNotEqual(po_picking, so_picking)
        self.assertNotEqual(
            po_picking.move_ids.quantity,
            so_picking.move_ids.quantity,
        )

        so_picking.with_user(self.user_company_b).button_validate()
        self.assertEqual(so_picking.state, "done")
        po_internal_pick = po_picking.move_ids.move_dest_ids.picking_id
        # the move in the receipt should have a "next move" due to "two_steps"
        self.assertTrue(purchase.picking_ids.move_ids.move_dest_ids)
        self.assertEqual(len(sale.picking_ids), 3)  # Pick + Backorder + Delivery
        self.assertTrue(
            all((po_picking, po_internal_pick, so_picking, so_internal_pick))
        )
        # Quantities should have been synced
        self.assertNotEqual(po_picking, so_picking)
        self.assertEqual(
            po_picking.move_ids.quantity,
            so_picking.move_ids.quantity,
        )

        # Check picking state
        self.assertEqual(po_picking.state, so_picking.state)

        # An additional receipt should have been created for the PO
        self.assertEqual(len(purchase.picking_ids), 2)
        done_purchase_picking = purchase.picking_ids.filtered(
            lambda x: x.state == "done"
        )
        self.assertEqual(len(done_purchase_picking), 1)
        self.assertEqual(done_purchase_picking, po_picking)
        new_receipt_picking = done_purchase_picking._get_next_transfers()
        self.assertEqual(len(new_receipt_picking), 1)
        self.assertEqual(new_receipt_picking.state, "assigned")

    def test_sync_picking_multi_step_with_transit(self):
        """
        Test that the lot is synchronized on the moves
        when using inter-company transit locations
        and warehouses are configured with multi-step routes.
        company B: Sale picking
            Picking 1: from Stock to Packing
            Picking 2: from Packing to Transit Location
        company A: Purchase picking
            Picking 1: from Transit Location to Input
            Picking 2: from Input to Stock
        """
        self.company_a.sync_picking = True
        self.warehouse_a.reception_steps = "two_steps"
        self.company_b.sync_picking = True
        self.warehouse_c.delivery_steps = "pick_ship"
        # Set inter-company locations on partners
        interco_location = self.env.ref("stock.stock_location_inter_company")
        self.partner_company_b.with_company(self.company_a).write(
            {
                "property_stock_customer": interco_location.id,
                "property_stock_supplier": interco_location.id,
            }
        )
        self.partner_company_a.with_company(self.company_b).write(
            {
                "property_stock_customer": interco_location.id,
                "property_stock_supplier": interco_location.id,
            }
        )
        purchase = self._create_purchase_order(
            self.partner_company_b, self.stockable_product_serial
        )
        sale = self._approve_po(purchase)
        self.assertEqual(len(purchase.picking_ids), 1)
        # Only a single picking is created for the sale.
        # When this picking is validated, two pickings should be created:
        # one for the backorder and one for the delivery.
        self.assertEqual(len(sale.picking_ids), 1)
        # Check the locations
        self.assertEqual(purchase.picking_ids.location_id.usage, "transit")
        self.assertEqual(purchase.picking_ids.location_dest_id.usage, "internal")
        self.assertEqual(sale.picking_ids.location_id.usage, "internal")
        self.assertEqual(sale.picking_ids.location_dest_id.usage, "internal")
        self.assertEqual(sale.picking_ids.move_ids.location_final_id.usage, "transit")
        # validate the SO internal picking
        so_internal_pick = sale.picking_ids
        so_move = so_internal_pick.move_ids
        so_move.move_line_ids = [
            Command.clear(),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_1.id,
                    "picking_id": so_internal_pick.id,
                },
            ),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_2.id,
                    "picking_id": so_internal_pick.id,
                },
            ),
            Command.create(
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "quantity": 1,
                    "lot_id": self.serial_3.id,
                    "picking_id": so_internal_pick.id,
                },
            ),
        ]
        so_internal_pick.with_user(self.user_company_b).button_validate()
        self.assertEqual(so_internal_pick.state, "done")
        po_picking = purchase.picking_ids
        # check po_picking state
        self.assertEqual(po_picking.state, "waiting")
        # validate the SO picking
        so_picking = sale.picking_ids.filtered(
            lambda x: x.location_dest_id.usage == "customer"
        )
        so_picking.with_user(self.user_company_b).button_validate()
        self.assertEqual(so_picking.state, "done")
        # The location at the picking level is set to Customer by the operation type,
        # but at the move level, it is Transit.
        self.assertEqual(so_picking.location_dest_id.usage, "customer")
        self.assertEqual(so_picking.move_ids.location_dest_id.usage, "transit")
        # the move in the receipt should have a "next move" due to "two_steps"
        self.assertTrue(purchase.picking_ids.move_ids.move_dest_ids)
        self.assertEqual(len(sale.picking_ids), 2)  # Pick + Delivery
        # Quantities should have been synced
        self.assertEqual(
            po_picking.move_ids.quantity,
            so_picking.move_ids.quantity,
        )
        # Check picking state
        self.assertEqual(po_picking.state, "done")
        new_receipt_picking = po_picking._get_next_transfers()
        self.assertEqual(len(new_receipt_picking), 1)
        self.assertEqual(new_receipt_picking.state, "assigned")
        # check the lots
        so_lots = so_move.mapped("move_line_ids.lot_id")
        po_lots = po_picking.mapped("move_ids.move_line_ids.lot_id")
        self.assertEqual(
            so_lots, po_lots, msg="The lots of the moves should be the same"
        )
        self.assertFalse(so_lots.company_id, msg="Lots should not have a company.")
