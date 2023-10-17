# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestStockIntercompany(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_demo = cls.env.ref("base.user_demo")
        company_obj = cls.env["res.company"]
        # Create 2 companies and configure intercompany picking type param on them
        cls.company1 = company_obj.search(
            [("name", "=", "Company A")]
        ) or company_obj.create({"name": "Company A"})
        cls.company2 = company_obj.search(
            [("name", "=", "Company B")]
        ) or company_obj.create({"name": "Company B"})
        cls.picking_type_out_company1 = (
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
        cls.picking_type_out_company2 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [
                    ("company_id", "=", cls.company2.id),
                    ("name", "=", "Delivery Orders"),
                ],
                limit=1,
            )
        )
        cls.picking_type_in_company1 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [("company_id", "=", cls.company1.id), ("name", "=", "Receipts")],
                limit=1,
            )
        )
        cls.picking_type_in_company2 = (
            cls.env["stock.picking.type"]
            .sudo()
            .search(
                [("company_id", "=", cls.company2.id), ("name", "=", "Receipts")],
                limit=1,
            )
        )

        cls.company1.intercompany_in_type_id = cls.picking_type_in_company1.id
        cls.company2.intercompany_in_type_id = cls.picking_type_in_company2.id

        cls.company1.intercompany_out_type_id = cls.picking_type_out_company1.id
        cls.company2.intercompany_out_type_id = cls.picking_type_out_company2.id
        # assign both companies to current user
        cls.user_demo.write(
            {
                "company_id": cls.company1.id,
                "company_ids": [(4, cls.company1.id), (4, cls.company2.id)],
            }
        )
        # create storable product
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
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

    def test_picking_creation_same_company(self):
        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company1.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": self.env.ref(
                        "stock.stock_location_customers"
                    ).id,
                    "picking_type_id": self.picking_type_out_company1.id,
                }
            )
        )

        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking.id,
            }
        )

        picking.action_confirm()
        picking.button_validate()

        company_pickings = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .sudo()
            .search(
                [
                    (
                        "picking_type_id",
                        "in",
                        [
                            self.picking_type_in_company1.id,
                            self.picking_type_out_company1.id,
                        ],
                    )
                ]
            )
        )

        self.assertEqual(len(company_pickings), 1)
        self.assertEqual(company_pickings, picking)
        self.assertFalse(company_pickings.intercompany_parent_id)

    def test_picking_creation_in(self):
        # Create an un when an out is created
        self.assertEquals(
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search_count([("picking_type_id", "=", self.picking_type_in_company2.id)]),
            0,
        )

        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": self.env.ref(
                        "stock.stock_location_customers"
                    ).id,
                    "picking_type_id": self.picking_type_out_company1.id,
                }
            )
        )

        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking.id,
            }
        )

        picking.action_confirm()
        picking.button_validate()

        counterpart_pickings = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_in_company2.id)])
        )

        self.assertEqual(len(counterpart_pickings), 1)
        self.assertNotEqual(counterpart_pickings, picking)
        self.assertEqual(counterpart_pickings.intercompany_parent_id, picking)
        self.assertEqual(picking.intercompany_child_ids[0], counterpart_pickings)

    def test_picking_creation_out(self):
        self.company2.intercompany_picking_creation_mode = "out"
        # Create an out when an in is created

        self.assertEquals(
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search_count(
                [("picking_type_id", "=", self.picking_type_out_company2.id)]
            ),
            0,
        )

        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.env.ref("stock.stock_location_suppliers").id,
                    "location_dest_id": self.stock_location.id,
                    "picking_type_id": self.picking_type_in_company1.id,
                }
            )
        )

        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_suppliers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking.id,
            }
        )

        picking.action_confirm()

        counterpart_pickings = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_out_company2.id)])
        )

        self.assertEqual(len(counterpart_pickings), 1)
        self.assertNotEqual(counterpart_pickings, picking)
        self.assertEqual(counterpart_pickings.intercompany_parent_id, picking)
        self.assertEqual(picking.intercompany_child_ids[0], counterpart_pickings)

    def test_picking_creation_in_wrong_mode(self):
        self.company2.intercompany_picking_creation_mode = "out"
        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": self.env.ref(
                        "stock.stock_location_customers"
                    ).id,
                    "picking_type_id": self.picking_type_out_company1.id,
                }
            )
        )

        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking.id,
            }
        )

        picking.action_confirm()
        picking.button_validate()

        counterpart_pickings = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_in_company2.id)])
        )

        self.assertEqual(len(counterpart_pickings), 0)

    def test_picking_creation_out_wrong_mode(self):
        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.env.ref("stock.stock_location_suppliers").id,
                    "location_dest_id": self.stock_location.id,
                    "picking_type_id": self.picking_type_in_company1.id,
                }
            )
        )

        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_suppliers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking.id,
            }
        )

        picking.action_confirm()

        counterpart_pickings = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_out_company2.id)])
        )

        self.assertEqual(len(counterpart_pickings), 0)

    def test_picking_creation_in_mode_both(self):
        self.company2.intercompany_picking_creation_mode = "both"

        self.assertEquals(
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search_count(
                [
                    (
                        "picking_type_id",
                        "in",
                        [
                            self.picking_type_in_company2.id,
                            self.picking_type_out_company2.id,
                        ],
                    )
                ]
            ),
            0,
        )

        picking_out = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": self.env.ref(
                        "stock.stock_location_customers"
                    ).id,
                    "picking_type_id": self.picking_type_out_company1.id,
                }
            )
        )

        picking_in = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.env.ref("stock.stock_location_suppliers").id,
                    "location_dest_id": self.stock_location.id,
                    "picking_type_id": self.picking_type_in_company1.id,
                }
            )
        )
        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking_out.id,
            }
        )

        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_suppliers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking_in.id,
            }
        )
        picking_out.action_confirm()
        picking_out.button_validate()
        picking_in.action_confirm()

        counterpart_pickings_in = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_in_company2.id)])
        )
        counterpart_pickings_out = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_out_company2.id)])
        )

        self.assertEqual(len(counterpart_pickings_in), 1)
        self.assertEqual(len(counterpart_pickings_out), 1)
        self.assertNotEqual(counterpart_pickings_in, picking_out)
        self.assertNotEqual(counterpart_pickings_out, picking_in)
        self.assertEqual(counterpart_pickings_in.intercompany_parent_id, picking_out)
        self.assertEqual(counterpart_pickings_out.intercompany_parent_id, picking_in)
        self.assertEqual(picking_out.intercompany_child_ids[0], counterpart_pickings_in)
        self.assertEqual(picking_in.intercompany_child_ids[0], counterpart_pickings_out)

    def test_picking_creation_in_mode_none(self):
        self.company2.intercompany_picking_creation_mode = False

        self.assertEquals(
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search_count(
                [
                    (
                        "picking_type_id",
                        "in",
                        [
                            self.picking_type_in_company2.id,
                            self.picking_type_out_company2.id,
                        ],
                    )
                ]
            ),
            0,
        )

        picking_out = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": self.env.ref(
                        "stock.stock_location_customers"
                    ).id,
                    "picking_type_id": self.picking_type_out_company1.id,
                }
            )
        )

        picking_in = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "location_id": self.env.ref("stock.stock_location_suppliers").id,
                    "location_dest_id": self.stock_location.id,
                    "picking_type_id": self.picking_type_in_company1.id,
                }
            )
        )
        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking_out.id,
            }
        )

        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_suppliers").id,
                "product_id": self.product1.id,
                "product_uom_id": self.uom_unit.id,
                "qty_done": 1.0,
                "picking_id": picking_in.id,
            }
        )
        picking_out.action_confirm()
        picking_out.button_validate()
        picking_in.action_confirm()

        self.assertEquals(
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search_count(
                [
                    (
                        "picking_type_id",
                        "in",
                        [
                            self.picking_type_in_company2.id,
                            self.picking_type_out_company2.id,
                        ],
                    )
                ]
            ),
            0,
        )
