# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import Form

from odoo.addons.purchase_sale_inter_company.tests import (
    test_inter_company_purchase_sale as test_icps,
)

TestPurchaseSaleInterCompany = test_icps.TestPurchaseSaleInterCompany


class TestPurchaseSaleStockInterCompany(TestPurchaseSaleInterCompany):
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
                    "location_id": cls.warehouse_a.lot_stock_id.id,
                    "quantity": 1,
                    "lot_id": lot.id,
                }
            )
        return lot

    @classmethod
    def _create_purchase_order_for_stockable_product_serial(cls, partner, quantity=1):
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        with po.order_line.new() as line_form:
            line_form.product_id = cls.stockable_product_serial
            line_form.product_qty = quantity
            line_form.price_unit = 450.0
        return po.save()

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
        cls.product = cls.product_consultant_multi_company
        cls.consumable_product = cls.env["product.product"].create(
            {
                "name": "Consumable Product",
                "type": "consu",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "qty_available": 100,
                "company_id": False,
            }
        )
        cls.stockable_product = cls.env["product.product"].create(
            {
                "name": "Stockable Product",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "company_id": False,
            }
        )
        cls.stockable_product_serial = cls.env["product.product"].create(
            {
                "name": "Stockable Product Tracked by Serial",
                "type": "product",
                "tracking": "serial",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "company_id": False,
            }
        )
        cls.stockable_product_serial_2 = cls.env["product.product"].create(
            {
                "name": "Stockable Product Tracked by Serial 2",
                "type": "product",
                "tracking": "serial",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "company_id": False,
            }
        )
        # if partner_multi_company or product_multi_company is installed
        # We have to do that because the default method added a company
        if "company_id" in cls.env["product.template"]._fields:
            cls.product.company_id = False
            cls.consumable_product.company_id = False
            cls.stockable_product.company_id = False
            cls.stockable_product_serial.company_id = False

        # Add quants for product tracked by serial to supplier
        cls.serial_1 = cls._create_serial_and_quant(
            cls.stockable_product_serial, "111", cls.company_b
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
        cls.serial_6 = cls._create_serial_and_quant(
            cls.stockable_product_serial_2, "666", cls.company_b
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
        self.product.type = "product"
        self.partner_company_b.company_id = False
        purchase = self.purchase_company_a
        sale = self._approve_po()
        sale_picking = sale.picking_ids[0]
        sale_picking.with_company(sale_picking.company_id).action_confirm()
        sale_picking.move_ids.quantity = 1.0
        res_dict = sale_picking.with_company(sale_picking.company_id).button_validate()
        if isinstance(res_dict, dict) and "context" in res_dict:
            self.env["stock.backorder.confirmation"].with_context(
                **res_dict["context"]
            ).process()
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
        self.product.type = "product"
        self.partner_company_b.company_id = False
        self.product2 = self.env["product.product"].create(
            {"name": "Product 2", "type": "product"}
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

    def test_sync_picking_lot_and_qty_with_move_diff(self):
        """
        Create a purchase order with 3 lines for 3 different products:
        - stockable product tracked by serial (1): 1 qty
        - stockable product tracked by serial (2): 3 qty
        - stockable product (not tracked by serial): 50 qty
        In the delivery, having this:
        - stockable product tracked by serial (1): 2 move lines with 1 lot each
        - stockable product tracked by serial (2): 1 move line with 1 lot
        - stockable product (not tracked by serial): 1 move line with 30 qty and no lot
        Expected to have the same move lines in the receipt
        """
        po_form = Form(self.env["purchase.order"])
        po_form.company_id = self.company_a
        po_form.partner_id = self.partner_company_b

        with po_form.order_line.new() as line_form:
            line_form.product_id = self.stockable_product_serial
            line_form.product_qty = 1
            line_form.price_unit = 450.0
        with po_form.order_line.new() as line_form:
            line_form.product_id = self.stockable_product_serial_2
            line_form.product_qty = 3
            line_form.price_unit = 450.0
        with po_form.order_line.new() as line_form:
            line_form.product_id = self.stockable_product
            line_form.product_qty = 50
            line_form.price_unit = 1000.0
        self.purchase_company_a = po_form.save()

        purchase = self.purchase_company_a
        sale = self._approve_po()

        # validate the SO picking
        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids
        so_moves = so_picking_id.move_ids
        for move in so_moves:
            if move.product_id == self.stockable_product_serial:
                move.move_line_ids = [
                    Command.create(
                        {
                            "location_id": move.location_id.id,
                            "location_dest_id": move.location_dest_id.id,
                            "product_id": self.stockable_product_serial.id,
                            "quantity": 1,
                            "lot_id": self.serial_1.id,
                            "picking_id": so_picking_id.id,
                        }
                    ),
                    Command.create(
                        {
                            "location_id": move.location_id.id,
                            "location_dest_id": move.location_dest_id.id,
                            "product_id": self.stockable_product_serial.id,
                            "quantity": 1,
                            "lot_id": self.serial_2.id,
                            "picking_id": so_picking_id.id,
                        }
                    ),
                ]
            elif move.product_id == self.stockable_product_serial_2:
                move.move_line_ids = [
                    Command.create(
                        {
                            "location_id": move.location_id.id,
                            "location_dest_id": move.location_dest_id.id,
                            "product_id": self.stockable_product_serial_2.id,
                            "quantity": 1,
                            "lot_id": self.serial_6.id,
                            "picking_id": so_picking_id.id,
                        }
                    ),
                ]
            elif move.product_id == self.stockable_product:
                move.move_line_ids = [
                    Command.create(
                        {
                            "location_id": move.location_id.id,
                            "location_dest_id": move.location_dest_id.id,
                            "product_id": self.stockable_product.id,
                            "quantity": 30,
                            "lot_id": False,  # No lot for stockable product
                            "picking_id": so_picking_id.id,
                        }
                    ),
                ]
        res_dict = so_picking_id.with_company(
            so_picking_id.company_id
        ).button_validate()
        if isinstance(res_dict, dict) and "context" in res_dict:
            self.env["stock.backorder.confirmation"].with_context(
                **res_dict["context"]
            ).process()

        products = so_moves.mapped("product_id") | po_picking_id.move_ids.mapped(
            "product_id"
        )
        for product in products:
            p_so_moves = so_moves.filtered(lambda m, p=product: m.product_id == p)
            p_po_moves = po_picking_id.move_ids.filtered(
                lambda m, p=product: m.product_id == p
            )
            so_lots = p_so_moves.mapped("move_line_ids.lot_id")
            po_lots = p_po_moves.mapped("move_line_ids.lot_id")
            # test if quantity, lots are synchronized in stock move lines
            self.assertEqual(
                len(p_so_moves.move_line_ids),
                len(p_po_moves.move_line_ids),
                msg="The number of move lines should be the same on both moves",
            )
            self.assertEqual(
                len(so_lots),
                len(po_lots),
                msg="There aren't the same number of lots on both moves",
            )
            self.assertEqual(
                sum(p_so_moves.move_line_ids.mapped("quantity")),
                sum(p_po_moves.move_line_ids.mapped("quantity")),
                msg="The quantities of the move lines should be the same",
            )
            if product in (
                self.stockable_product_serial,
                self.stockable_product_serial_2,
            ):
                self.assertNotEqual(
                    so_lots,
                    po_lots,
                    msg="The lots of the moves should be different objects",
                )
                self.assertEqual(
                    so_lots.mapped("name"),
                    po_lots.mapped("name"),
                    msg="The lots should have the same name in both moves",
                )
                for lot in so_lots:
                    self.assertIn(
                        lot.name,
                        po_lots.mapped("name"),
                        msg=f"{lot.name} should have been synchronized in the purchase "
                        "order",
                    )
                for lot in po_lots:
                    self.assertIn(
                        lot.name,
                        so_lots.mapped("name"),
                        msg=f"{lot.name} should have been synchronized in the sale "
                        "order",
                    )
                self.assertEqual(
                    len(
                        p_so_moves.move_line_ids.filtered(
                            lambda ml: ml.lot_id and ml.quantity == 1
                        )
                    ),
                    len(
                        p_po_moves.move_line_ids.filtered(
                            lambda ml: ml.lot_id and ml.quantity == 1
                        )
                    ),
                    msg="There should be the same number of move lines with lot and "
                    "quantity 1 for the serial product",
                )
            elif product == self.stockable_product:
                self.assertEqual(
                    len(p_so_moves.move_line_ids.filtered(lambda ml: not ml.lot_id)),
                    1,
                    msg="There should be one move line without lot for the stockable "
                    "product",
                )
                self.assertEqual(
                    p_so_moves.move_line_ids.filtered(
                        lambda ml: not ml.lot_id
                    ).quantity,
                    30,
                    msg="The quantity of the move line without lot should be 30",
                )

    def test_intercompany_picking_id_assignment(self):
        self.product.type = "product"
        sale = self._approve_po()
        so_picking = sale.picking_ids[0]
        po_picking = self.purchase_company_a.picking_ids[0]
        po_picking_pending = po_picking.filtered(
            lambda x: x.state not in ["done", "cancel"]
        )
        self.assertFalse(so_picking.intercompany_picking_id)
        so_picking.sudo()._set_intercompany_picking_qty_and_lot(self.purchase_company_a)
        self.assertEqual(po_picking_pending.intercompany_picking_id, so_picking)
        self.assertEqual(so_picking.intercompany_picking_id, po_picking_pending)

    def test_action_done_without_purchase(self):
        self.product.type = "product"
        sale = self.env["sale.order"]
        with Form(sale) as sale_form:
            sale_form.company_id = self.company_a
            sale_form.partner_id = self.partner_company_b
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
            line_form.price_unit = 100.0
        sale = sale_form.save()
        sale.action_confirm()
        self.assertFalse(sale.auto_purchase_order_id)
        sale_picking = sale.picking_ids[0]
        move = sale_picking.move_ids
        move.move_line_ids = [
            Command.create(
                {
                    "location_id": move.location_id.id,
                    "location_dest_id": move.location_dest_id.id,
                    "product_id": self.product.id,
                    "quantity": 1,
                    "picking_id": sale_picking.id,
                }
            ),
        ]
        res_dict = sale_picking.with_company(sale_picking.company_id).button_validate()
        if isinstance(res_dict, dict) and "context" in res_dict:
            self.env["stock.backorder.confirmation"].with_context(
                **res_dict["context"]
            ).process()
