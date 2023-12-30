# Copyright (C) 2023 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import RecordCapturer, TransactionCase


class TestIntercompanyBidirectional(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user_demo = self.env["res.users"].create(
            {
                "login": "firstnametest",
                "name": "User Demo",
                "email": "firstnametest@example.org",
                "groups_id": [
                    (4, self.env.ref("base.group_user").id),
                    (4, self.env.ref("stock.group_stock_user").id),
                ],
            }
        )
        company_obj = self.env["res.company"]
        # Create 2 companies and configure intercompany picking type param on them
        self.company1 = company_obj.create({"name": "Company A"})
        self.company2 = company_obj.create({"name": "Company B"})
        self.picking_type_1 = (
            self.env["stock.picking.type"]
            .sudo()
            .search(
                [
                    ("company_id", "=", self.company1.id),
                    ("name", "=", "Delivery Orders"),
                ],
                limit=1,
            )
        )
        self.picking_type_2 = (
            self.env["stock.picking.type"]
            .sudo()
            .search(
                [("company_id", "=", self.company1.id), ("name", "=", "Receipts")],
                limit=1,
            )
        )

        self.picking_type_11 = (
            self.env["stock.picking.type"]
            .sudo()
            .search(
                [
                    ("company_id", "=", self.company2.id),
                    ("name", "=", "Delivery Orders"),
                ],
                limit=1,
            )
        )
        self.picking_type_22 = (
            self.env["stock.picking.type"]
            .sudo()
            .search(
                [("company_id", "=", self.company2.id), ("name", "=", "Receipts")],
                limit=1,
            )
        )

        self.company1.intercompany_out_type_id = self.picking_type_1.id
        self.company1.intercompany_in_type_id = self.picking_type_2.id
        self.company1.auto_update_qty_done = True
        self.company1.move_packages = True
        self.company1.mirror_lot_numbers = True
        self.company2.intercompany_out_type_id = self.picking_type_11.id
        self.company2.intercompany_in_type_id = self.picking_type_22.id
        self.company2.auto_update_qty_done = True
        self.company2.move_packages = True
        self.company2.mirror_lot_numbers = True
        # assign both companies to current user
        self.user_demo.write(
            {
                "company_id": self.company1.id,
                "company_ids": [(4, self.company1.id), (4, self.company2.id)],
            }
        )
        # create storable products
        product_obj = self.env["product.product"]
        self.product1 = product_obj.create(
            {
                "name": "Product A",
                "type": "product",
                "categ_id": self.env.ref("product.product_category_all").id,
                "qty_available": 100,
            }
        )
        self.product2 = product_obj.create(
            {
                "name": "Product B",
                "type": "product",
                "categ_id": self.env.ref("product.product_category_all").id,
                "qty_available": 60,
            }
        )
        self.product3 = product_obj.create(
            {
                "name": "Product C",
                "type": "product",
                "categ_id": self.env.ref("product.product_category_all").id,
                "qty_available": 40,
            }
        )
        self.product4 = product_obj.create(
            {
                "name": "Product D",
                "type": "product",
                "tracking": "serial",
                "categ_id": self.env.ref("product.product_category_all").id,
                "qty_available": 1,
            }
        )
        self.product5 = product_obj.create(
            {
                "name": "Product E",
                "type": "product",
                "tracking": "lot",
                "categ_id": self.env.ref("product.product_category_all").id,
                "qty_available": 4,
            }
        )
        self.stock_location = (
            self.env["stock.location"]
            .sudo()
            .search([("name", "=", "Stock"), ("company_id", "=", self.company1.id)])
        )
        self.uom_unit = self.env.ref("uom.product_uom_unit")

    def test_picking_creation(self):
        custs_location = self.env.ref("stock.stock_location_customers")
        custs_location.company_id = False
        self.product1.company_id = False

        # Create an outgoing picking
        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": custs_location.id,
                    "picking_type_id": self.company1.intercompany_out_type_id.id,
                }
            )
        )
        self.env["stock.move.line"].create(
            {
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking.id,
            }
        )
        # Retrieve the captured counterpart picking
        with RecordCapturer(self.env["stock.picking"], []) as rc:
            picking.action_confirm()
            picking.button_validate()

        counterpart_picking = rc.records
        self.assertEqual(counterpart_picking.partner_id.id, self.company1.partner_id.id)
        self.assertEqual(len(counterpart_picking), 1)
        self.assertEqual(counterpart_picking.counterpart_of_picking_id, picking)
        self.assertEqual(len(counterpart_picking.move_ids), len(picking.move_ids))
        for cp_move, move in zip(counterpart_picking.move_ids, picking.move_ids):
            self.assertEqual(cp_move.counterpart_of_move_id, move)
        self.assertEqual(
            len(counterpart_picking.move_line_ids), len(picking.move_line_ids)
        )
        for cp_line, line in zip(
            counterpart_picking.move_line_ids, picking.move_line_ids
        ):
            self.assertEqual(cp_line.counterpart_of_line_id, line)
        for cp_line, line in zip(
            counterpart_picking.move_line_ids, picking.move_line_ids
        ):
            self.assertEqual(cp_line.qty_done, line.qty_done)

    def test_picking_creation_move_packages(self):
        custs_location = self.env.ref("stock.stock_location_customers")
        supplier_location = self.env.ref("stock.stock_location_suppliers")
        custs_location.company_id = False
        self.product1.company_id = False

        # Move entire packages which come from vendors
        # Create an incoming picking
        incoming_picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": supplier_location.id,
                    "location_dest_id": self.stock_location.id,
                    "picking_type_id": self.company1.intercompany_in_type_id.id,
                }
            )
        )
        # Create a move line for the incoming picking
        self.env["stock.move.line"].create(
            {
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 3.0,
                "picking_id": incoming_picking.id,
            }
        )
        # Put in pack, in order to use this package for testing the move packages logic
        incoming_picking.action_put_in_pack()
        incoming_picking.action_confirm()
        incoming_picking.button_validate()

        # Retrieve the package_id associated with the incoming picking
        package_id = (
            self.env["stock.package_level"]
            .search([("picking_id", "=", incoming_picking.id)])
            .package_id
        )

        # Create an outgoing picking
        outgoing_picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": custs_location.id,
                    "picking_type_id": self.company1.intercompany_out_type_id.id,
                }
            )
        )
        package_level = self.env["stock.package_level"].create(
            {
                "package_id": package_id.id,
                "picking_id": outgoing_picking.id,
                "company_id": self.company1.id,
                "location_id": self.stock_location.id,
            }
        )
        package_level.write({"is_done": True})
        with RecordCapturer(
            self.env["stock.picking"].with_context(default_company_id=self.company2.id),
            [],
        ) as rc:
            outgoing_picking.action_confirm()
            outgoing_picking.button_validate()

        # Retrieve the captured counterpart picking
        counterpart_picking = rc.records

        self.assertEqual(counterpart_picking.partner_id.id, self.company1.partner_id.id)
        self.assertEqual(len(counterpart_picking), 1)
        self.assertEqual(
            counterpart_picking.counterpart_of_picking_id, outgoing_picking
        )
        self.assertEqual(
            len(counterpart_picking.package_level_ids),
            len(outgoing_picking.package_level_ids),
        )

        for cp_line, line in zip(
            counterpart_picking.move_line_ids, outgoing_picking.move_line_ids
        ):
            self.assertEqual(line.result_package_id.id, False)
            self.assertEqual(cp_line.result_package_id.id, package_id.id)

        # Confirm and validate the counterpart picking
        counterpart_picking.action_confirm()
        counterpart_picking.button_validate()
        self.assertEqual(counterpart_picking.state, "done")
        self.assertEqual(
            package_id.location_id.id, counterpart_picking.location_dest_id.id
        )

    def test_picking_creation_move_products_in_package(self):
        custs_location = self.env.ref("stock.stock_location_customers")
        supplier_location = self.env.ref("stock.stock_location_suppliers")
        custs_location.company_id = False
        self.product1.company_id = False

        # Intercompany Move of products in package
        # Create an incoming picking
        incoming_picking2 = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": supplier_location.id,
                    "location_dest_id": self.stock_location.id,
                    "picking_type_id": self.company1.intercompany_in_type_id.id,
                }
            )
        )
        # Create a move lines for the incoming picking
        self.env["stock.move.line"].create(
            [
                {
                    "product_id": self.product2.id,
                    "product_uom_id": self.uom_unit.id,
                    "qty_done": 2.0,
                    "picking_id": incoming_picking2.id,
                },
                {
                    "product_id": self.product3.id,
                    "product_uom_id": self.uom_unit.id,
                    "qty_done": 3.0,
                    "picking_id": incoming_picking2.id,
                },
            ]
        )
        incoming_picking2.action_confirm()
        incoming_picking2.button_validate()

        # Create an outgoing picking
        outgoing_picking2 = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": custs_location.id,
                    "picking_type_id": self.company1.intercompany_out_type_id.id,
                }
            )
        )
        # Create a move lines for the outgoing picking
        self.env["stock.move.line"].create(
            [
                {
                    "product_id": self.product2.id,
                    "product_uom_id": self.uom_unit.id,
                    "qty_done": 2.0,
                    "picking_id": outgoing_picking2.id,
                },
                {
                    "product_id": self.product3.id,
                    "product_uom_id": self.uom_unit.id,
                    "qty_done": 3.0,
                    "picking_id": outgoing_picking2.id,
                },
            ]
        )

        # Put in pack, in order to use this package for testing the move packages logic
        outgoing_picking2.action_put_in_pack()

        # Retrieve the package_id associated with the incoming picking
        package_id = (
            self.env["stock.package_level"]
            .search([("picking_id", "=", outgoing_picking2.id)])
            .package_id
        )

        with RecordCapturer(
            self.env["stock.picking"].with_context(default_company_id=self.company2.id),
            [],
        ) as rc:
            outgoing_picking2.action_confirm()
            outgoing_picking2.button_validate()

        # Retrieve the captured counterpart picking
        counterpart_picking2 = rc.records

        self.assertEqual(
            counterpart_picking2.partner_id.id, self.company1.partner_id.id
        )
        self.assertEqual(len(counterpart_picking2), 1)
        self.assertEqual(
            counterpart_picking2.counterpart_of_picking_id, outgoing_picking2
        )
        self.assertEqual(
            len(counterpart_picking2.package_level_ids),
            len(outgoing_picking2.package_level_ids),
        )

        for cp_line, line in zip(
            counterpart_picking2.move_line_ids, outgoing_picking2.move_line_ids
        ):
            self.assertEqual(line.result_package_id.id, False)
            self.assertEqual(cp_line.result_package_id.id, package_id.id)

        # Confirm and validate the counterpart picking
        counterpart_picking2.action_confirm()
        counterpart_picking2.button_validate()
        self.assertEqual(counterpart_picking2.state, "done")
        self.assertEqual(
            package_id.location_id.id, counterpart_picking2.location_dest_id.id
        )

    def test_picking_creation_mirror_lot_numbers(self):
        custs_location = self.env.ref("stock.stock_location_customers")
        supplier_location = self.env.ref("stock.stock_location_suppliers")
        custs_location.company_id = False
        self.product1.company_id = False

        # Create an incoming picking with lot and SN products
        incoming_picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": supplier_location.id,
                    "location_dest_id": self.stock_location.id,
                    "picking_type_id": self.company1.intercompany_in_type_id.id,
                }
            )
        )
        # Create a move lines for the incoming picking
        self.env["stock.move.line"].create(
            [
                {
                    "product_id": self.product4.id,
                    "product_uom_id": self.uom_unit.id,
                    "qty_done": 1.0,
                    "lot_name": "SN1000",
                    "picking_id": incoming_picking.id,
                },
                {
                    "product_id": self.product5.id,
                    "product_uom_id": self.uom_unit.id,
                    "qty_done": 1.0,
                    "lot_name": "LOT1000",
                    "picking_id": incoming_picking.id,
                },
            ]
        )
        incoming_picking.action_confirm()
        incoming_picking.button_validate()

        # Create an outgoing picking
        outgoing_picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": custs_location.id,
                    "picking_type_id": self.company1.intercompany_out_type_id.id,
                }
            )
        )
        lot_product4 = self.env["stock.lot"].search(
            [("name", "=", "SN1000"), ("product_id", "=", self.product4.id)]
        )
        lot_product5 = self.env["stock.lot"].search(
            [("name", "=", "LOT1000"), ("product_id", "=", self.product5.id)]
        )
        # Create a move lines for the outgoing picking with the received lot and SN products
        self.env["stock.move.line"].create(
            [
                {
                    "product_id": self.product4.id,
                    "product_uom_id": self.uom_unit.id,
                    "qty_done": 1.0,
                    "lot_id": lot_product4.id,
                    "picking_id": outgoing_picking.id,
                },
                {
                    "product_id": self.product5.id,
                    "product_uom_id": self.uom_unit.id,
                    "qty_done": 1.0,
                    "lot_id": lot_product5.id,
                    "picking_id": outgoing_picking.id,
                },
            ]
        )

        with RecordCapturer(
            self.env["stock.picking"].with_context(default_company_id=self.company2.id),
            [],
        ) as rc:
            outgoing_picking.action_confirm()
            outgoing_picking.button_validate()

        # Retrieve the captured counterpart picking
        counterpart_picking = rc.records

        self.assertEqual(counterpart_picking.partner_id.id, self.company1.partner_id.id)
        self.assertEqual(len(counterpart_picking), 1)
        self.assertEqual(
            counterpart_picking.counterpart_of_picking_id, outgoing_picking
        )
        # Check if the lot and SN are created in the counterpart picking
        for cp_line, line in zip(
            counterpart_picking.move_line_ids, outgoing_picking.move_line_ids
        ):
            self.assertEqual(cp_line.lot_id.name, line.lot_id.name)

        # Confirm and validate the counterpart picking
        counterpart_picking.action_confirm()
        counterpart_picking.button_validate()
        self.assertEqual(counterpart_picking.state, "done")
