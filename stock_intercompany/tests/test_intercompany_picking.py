# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests.common import RecordCapturer

from odoo.addons.base.tests.common import BaseCommon


class TestIntercompanyDelivery(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company_obj = cls.env["res.company"]
        cls.company1 = company_obj.create({"name": "Company A"})
        cls.company2 = company_obj.create({"name": "Company B"})
        cls.user_demo = cls.env["res.users"].create(
            {
                "login": "firstnametest",
                "name": "User Demo",
                "email": "firstnametest@example.org",
                "company_id": cls.company1.id,
                "company_ids": [
                    Command.link(cls.company1.id),
                    Command.link(cls.company2.id),
                ],
                "groups_id": [
                    Command.link(cls.env.ref("base.group_user").id),
                    Command.link(cls.env.ref("stock.group_stock_user").id),
                ],
            }
        )
        cls.picking_type_1 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [
                    ("company_id", "=", cls.company1.id),
                    ("name", "=", "Delivery Orders"),
                ],
                limit=1,
            )
        )
        cls.picking_type_2 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [
                    ("company_id", "=", cls.company2.id),
                    ("name", "=", "Receipts"),
                ],
                limit=1,
            )
        )

        cls.company1.intercompany_in_type_id = cls.picking_type_1.id
        cls.company2.intercompany_in_type_id = cls.picking_type_2.id
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.env.ref("product.product_category_all").id,
                "qty_available": 100,
            }
        )
        cls.stock_location = (
            cls.env["stock.location"]
            .sudo()
            .search([("name", "=", "Stock"), ("company_id", "=", cls.company1.id)])
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

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
                "quantity": 1.0,
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
        for cp_move, move in zip(
            counterpart_picking.move_ids, picking.move_ids, strict=False
        ):
            self.assertEqual(cp_move.counterpart_of_move_id, move)
        self.assertEqual(
            len(counterpart_picking.move_line_ids), len(picking.move_line_ids)
        )
        for cp_line, line in zip(
            counterpart_picking.move_line_ids, picking.move_line_ids, strict=False
        ):
            self.assertEqual(cp_line.counterpart_of_line_id, line)
