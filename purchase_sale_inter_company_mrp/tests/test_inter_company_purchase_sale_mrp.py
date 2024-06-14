# Copyright 2024 Therp BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.purchase_sale_inter_company.tests.test_inter_company_purchase_sale import (
    TestPurchaseSaleInterCompany,
)


class TestPurchaseSaleInterCompanyMrp(TestPurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.kit_product = cls.env["product.product"].create(
            {
                "name": "Test kit product",
                "type": "product",
            }
        )
        cls.kit_product_serial = cls.env["product.product"].create(
            {
                "name": "Stockable Kit Product, Component Tracked by Serial",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )
        cls.kit_component_1 = cls.env["product.product"].create(
            {"name": "Test kit component 1", "type": "consu"}
        )
        cls.kit_component_2 = cls.env["product.product"].create(
            {"name": "Test kit component 2", "type": "consu"}
        )
        cls.kit_component_3_serial = cls.env["product.product"].create(
            {
                "name": "Test kit component 3 Serial",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.kit_bom = cls.env["mrp.bom"].create(
            {"product_tmpl_id": cls.kit_product.product_tmpl_id.id, "type": "phantom"}
        )
        cls.kit_bom.company_id = False
        cls.kit_bom_serial = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.kit_product_serial.product_tmpl_id.id,
                "type": "phantom",
            }
        )
        cls.kit_bom_serial.company_id = False
        cls.env["mrp.bom.line"].create(
            {
                "bom_id": cls.kit_bom.id,
                "product_id": cls.kit_component_1.id,
                "product_qty": 2,
            }
        )
        cls.env["mrp.bom.line"].create(
            {
                "bom_id": cls.kit_bom.id,
                "product_id": cls.kit_component_2.id,
                "product_qty": 2,
            }
        )
        cls.env["mrp.bom.line"].create(
            {
                "bom_id": cls.kit_bom_serial.id,
                "product_id": cls.kit_component_3_serial.id,
                "product_qty": 2,
            }
        )
        cls.env["mrp.bom.line"].create(
            {
                "bom_id": cls.kit_bom_serial.id,
                "product_id": cls.kit_component_2.id,
                "product_qty": 2,
            }
        )
        # Add quants for product tracked by serial to supplier
        cls.kit_serial_1 = cls._create_serial_and_quant(
            cls.kit_component_3_serial, "111", cls.company_b
        )
        cls.kit_serial_2 = cls._create_serial_and_quant(
            cls.kit_component_3_serial, "222", cls.company_b
        )
        cls.kit_serial_3 = cls._create_serial_and_quant(
            cls.kit_component_3_serial, "333", cls.company_b
        )

    def test_sync_picking_mrp(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(self.partner_company_b, self.kit_product)
        sale = self._approve_po(purchase)

        # paranoia
        self.assertEqual(sale.order_line.product_id, self.kit_product)
        self.assertEqual(purchase.order_line.product_id, self.kit_product)

        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids
        self.assertTrue(po_picking_id)
        self.assertTrue(so_picking_id)

        # kits are expanded
        self.assertGreater(len(po_picking_id.move_lines), len(purchase.order_line))
        self.assertGreater(len(so_picking_id.move_lines), len(sale.order_line))

        # check po_picking state
        self.assertEqual(po_picking_id.state, "waiting")

        # Fill 2 out of 3 items for the kit components
        for ml in so_picking_id.move_lines:
            ml.quantity_done = 2
        self.assertNotEqual(po_picking_id, so_picking_id)
        for ml, po_ml in zip(so_picking_id.move_lines, po_picking_id.move_lines):
            self.assertNotEqual(
                ml.quantity_done,
                po_ml.quantity_done,
            )
            self.assertEqual(
                ml.product_qty,
                po_ml.product_qty,
            )

        # Validate sale order, create backorder
        wizard_data = so_picking_id.with_user(self.user_company_b).button_validate()
        wizard = (
            self.env["stock.backorder.confirmation"]
            .with_context(**wizard_data.get("context"))
            .create({})
        )
        wizard.with_user(self.user_company_b).process()
        self.assertEqual(so_picking_id.state, "done")
        self.assertNotEqual((sale.picking_ids - so_picking_id).state, "done")

        # Quantities should have been synced
        self.assertNotEqual(po_picking_id, so_picking_id)
        for ml, po_ml in zip(so_picking_id.move_lines, po_picking_id.move_lines):
            self.assertEqual(
                ml.quantity_done,
                po_ml.quantity_done,
            )

        # Check picking state
        self.assertEqual(po_picking_id.state, so_picking_id.state)

        # A backorder should have been made for both
        self.assertTrue(len(sale.picking_ids) > 1)
        self.assertEqual(len(purchase.picking_ids), len(sale.picking_ids))

    def test_sync_picking_lot_mrp(self):
        """
        Test that the lot is synchronized on the moves
        by searching or creating a new lot in the company of destination
        """
        # lot 3 already exists in company_a
        serial_3_company_a = self._create_serial_and_quant(
            self.kit_component_3_serial,
            "333",
            self.company_a,
            quant=False,
        )
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.kit_product_serial
        )
        sale = self._approve_po(purchase)

        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids
        self.assertTrue(po_picking_id)
        self.assertTrue(so_picking_id)

        # kits are expanded in picking
        # TODO: what if kits are expanded in SO->PO ? This also happens, but how to simulate?
        self.assertGreater(len(po_picking_id.move_lines), len(purchase.order_line))
        self.assertGreater(len(so_picking_id.move_lines), len(sale.order_line))

        # validate the SO picking
        so_move_no_serial = so_picking_id.move_lines[1]
        so_move_no_serial.quantity_done = 2
        so_move = so_picking_id.move_lines[0]
        so_move.move_line_ids = [
            (
                0,
                0,
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.kit_component_3_serial.id,
                    "product_uom_id": self.kit_component_3_serial.uom_id.id,
                    "qty_done": 1,
                    "lot_id": self.kit_serial_1.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            (
                0,
                0,
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.kit_component_3_serial.id,
                    "product_uom_id": self.kit_component_3_serial.uom_id.id,
                    "qty_done": 1,
                    "lot_id": self.kit_serial_3.id,
                    "picking_id": so_picking_id.id,
                },
            ),
        ]

        # validate picking and create draft backorder
        wizard_data = so_picking_id.with_user(self.user_company_b).button_validate()
        wizard = (
            self.env["stock.backorder.confirmation"]
            .with_context(**wizard_data.get("context"))
            .create({})
        )
        wizard.process()
        self.assertEqual(so_picking_id.state, "done")
        self.assertNotEqual((sale.picking_ids - so_picking_id).state, "done")

        so_lots = so_move.mapped("move_line_ids.lot_id")
        po_lots = po_picking_id.mapped("move_lines.move_line_ids.lot_id")
        self.assertEqual(
            len(so_lots),
            len(po_lots),
            msg="There aren't the same number of lots on both moves",
        )
        self.assertNotEqual(
            so_lots, po_lots, msg="The lots of the moves should be different objects"
        )
        self.assertEqual(
            so_lots.sudo().mapped("name"),
            po_lots.sudo().mapped("name"),
            msg="The lots should have the same name in both moves",
        )
        self.assertIn(
            serial_3_company_a,
            po_lots,
            msg="Serial 333 already existed, a new one shouldn't have been created",
        )
