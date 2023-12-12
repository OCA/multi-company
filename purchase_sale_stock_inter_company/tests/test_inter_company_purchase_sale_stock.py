# Copyright 2013-Today Odoo SA
# Copyright 2019-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form

from odoo.addons.purchase_sale_inter_company.tests.test_inter_company_purchase_sale import (
    TestPurchaseSaleInterCompany,
)


class TestPurchaseSaleStockInterCompany(TestPurchaseSaleInterCompany):
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
    def _create_purchase_order(cls, partner, product_id=None):
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = partner

        with po.order_line.new() as line_form:
            line_form.product_id = product_id if product_id else cls.product
            line_form.product_qty = 3.0
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        return po.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lot_obj = cls.env["stock.production.lot"]
        cls.quant_obj = cls.env["stock.quant"]
        # Configure 2 Warehouse per company
        cls.warehouse_a = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_a.id)], limit=1
        )
        cls.warehouse_b = cls._create_warehouse("CA-WB", cls.company_a)

        cls.warehouse_c = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company_b.id)], limit=1
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
        cls.stockable_product_serial = cls.env["product.product"].create(
            {
                "name": "Stockable Product Tracked by Serial",
                "type": "product",
                "tracking": "serial",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "company_id": False,
            }
        )
        # if partner_multi_company or product_multi_company is installed
        # We have to do that because the default method added a company
        if "company_ids" in cls.env["product.template"]._fields:
            cls.product.company_ids = False
            cls.consumable_product.company_ids = False
            cls.stockable_product_serial.company_ids = False

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

    def test_deliver_to_warehouse_a(self):
        self.purchase_company_a.picking_type_id = self.warehouse_a.in_type_id
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(self.warehouse_a.partner_id, sale.partner_shipping_id)

    def test_deliver_to_warehouse_b(self):
        self.purchase_company_a.picking_type_id = self.warehouse_b.in_type_id
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(self.warehouse_b.partner_id, sale.partner_shipping_id)

    def test_send_from_warehouse_c(self):
        self.company_b.warehouse_id = self.warehouse_c
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(sale.warehouse_id, self.warehouse_c)

    def test_send_from_warehouse_d(self):
        self.company_b.warehouse_id = self.warehouse_d
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(sale.warehouse_id, self.warehouse_d)

    def test_purchase_sale_stock_inter_company(self):
        self.purchase_company_a.notes = "Test note"
        sale = self._approve_po(self.purchase_company_a)
        self.assertEqual(
            sale.partner_shipping_id,
            self.purchase_company_a.picking_type_id.warehouse_id.partner_id,
        )
        self.assertEqual(sale.warehouse_id, self.warehouse_c)

    def test_sync_picking_lot(self):
        """
        Test that the lot is synchronized on the moves
        by searching or creating a new lot in the company of destination
        """
        # lot 3 already exists in company_a
        serial_3_company_a = self._create_serial_and_quant(
            self.stockable_product_serial, "333", self.company_a, quant=False,
        )
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True

        purchase = self._create_purchase_order(
            self.partner_company_b, self.stockable_product_serial
        )
        sale = self._approve_po(purchase)

        # validate the SO picking
        po_picking_id = purchase.picking_ids
        so_picking_id = sale.picking_ids

        so_move = so_picking_id.move_lines
        so_move.move_line_ids = [
            (
                0,
                0,
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "qty_done": 1,
                    "lot_id": self.serial_1.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            (
                0,
                0,
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "qty_done": 1,
                    "lot_id": self.serial_2.id,
                    "picking_id": so_picking_id.id,
                },
            ),
            (
                0,
                0,
                {
                    "location_id": so_move.location_id.id,
                    "location_dest_id": so_move.location_dest_id.id,
                    "product_id": self.stockable_product_serial.id,
                    "product_uom_id": self.stockable_product_serial.uom_id.id,
                    "qty_done": 1,
                    "lot_id": self.serial_3.id,
                    "picking_id": so_picking_id.id,
                },
            ),
        ]
        so_picking_id.button_validate()

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
            so_lots.mapped("name"),
            po_lots.mapped("name"),
            msg="The lots should have the same name in both moves",
        )
        self.assertIn(
            serial_3_company_a,
            po_lots,
            msg="Serial 333 already existed, a new one shouldn't have been created",
        )
