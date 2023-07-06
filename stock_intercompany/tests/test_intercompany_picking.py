# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import RecordCapturer, TransactionCase


class TestIntercompanyDelivery(TransactionCase):
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
                [("company_id", "=", self.company2.id), ("name", "=", "Receipts")],
                limit=1,
            )
        )

        self.company1.intercompany_in_type_id = self.picking_type_1.id
        self.company2.intercompany_in_type_id = self.picking_type_2.id
        # assign both companies to current user
        self.user_demo.write(
            {
                "company_id": self.company1.id,
                "company_ids": [(4, self.company1.id), (4, self.company2.id)],
            }
        )
        # create storable product
        self.product1 = self.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "categ_id": self.env.ref("product.product_category_all").id,
                "qty_available": 100,
            }
        )
        self.stock_location = (
            self.env["stock.location"]
            .sudo()
            .search([("name", "=", "Stock"), ("company_id", "=", self.company1.id)])
        )
        self.uom_unit = self.env.ref("uom.product_uom_unit")

    def test_picking_creation(self):
        stock_location = self.env["stock.location"].search(
            [("usage", "=", "internal"), ("company_id", "=", self.company1.id)]
        )
        custs_location = self.env.ref("stock.stock_location_customers")
        custs_location.company_id = False
        self.product1.company_id = False
        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": stock_location.id,
                    "location_dest_id": custs_location.id,
                    "picking_type_id": self.company1.intercompany_in_type_id.id,
                }
            )
        )
        self.env["stock.move.line"].create(
            {
                "location_id": stock_location.id,
                "location_dest_id": custs_location.id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking.id,
            }
        )
        with RecordCapturer(self.env["stock.picking"], []) as rc:
            picking.action_confirm()
            picking.button_validate()

        counterpart_picking = rc.records
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
