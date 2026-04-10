# Copyright 2021 Camptocamp
# Copyright 2022 Akretion (Florian Mounier <florian.mounier@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import RecordCapturer

from odoo.addons.base.tests.common import BaseCommon


class TestIntercompanyCommon(BaseCommon):
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
                    Command.link(cls.env.ref("stock.group_stock_manager").id),
                ],
            }
        )
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
        cls.company1.intercompany_in_type_id = cls.picking_type_in_company1
        cls.company2.intercompany_in_type_id = cls.picking_type_in_company2
        cls.company1.intercompany_out_type_id = cls.picking_type_out_company1
        cls.company2.intercompany_out_type_id = cls.picking_type_out_company2

        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.env.ref("product.product_category_all").id,
                "qty_available": 100,
            }
        )
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Product B",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.env.ref("product.product_category_all").id,
                "qty_available": 50,
            }
        )
        cls.product3 = cls.env["product.product"].create(
            {
                "name": "Product C",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.env.ref("product.product_category_all").id,
                "qty_available": 5,
            }
        )
        cls.stock_location = (
            cls.env["stock.location"]
            .sudo()
            .search(
                [("name", "=", "Stock"), ("company_id", "=", cls.company1.id)],
                limit=1,
            )
        )
        cls.stock_location2 = (
            cls.env["stock.location"]
            .sudo()
            .search(
                [("name", "=", "Stock"), ("company_id", "=", cls.company2.id)],
                limit=1,
            )
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

    def _make_picking(
        self,
        company,
        partner,
        picking_type,
        location,
        location_dest,
        product=None,
        qty=1.0,
    ):
        """Helper: create, add a move line and confirm a picking."""
        product = product or self.product1
        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=company.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": partner.id,
                    "picking_type_id": picking_type.id,
                    "location_id": location.id,
                    "location_dest_id": location_dest.id,
                }
            )
        )
        self.env["stock.move.line"].create(
            {
                "location_id": location.id,
                "location_dest_id": location_dest.id,
                "product_id": product.id,
                "product_uom_id": self.uom_unit.id,
                "quantity": qty,
                "picking_id": picking.id,
            }
        )
        return picking


@tagged("post_install", "-at_install")
class TestIntercompanyDelivery(TestIntercompanyCommon):
    def test_picking_creation(self):
        stock_location = self.env["stock.location"].search(
            [("usage", "=", "internal"), ("company_id", "=", self.company1.id)],
            limit=1,
        )
        custs_location = self.env.ref("stock.stock_location_customers")
        custs_location.company_id = False
        self.product1.company_id = False
        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_out_company1,
            stock_location,
            custs_location,
        )
        with RecordCapturer(self.env["stock.picking"], []) as rc:
            picking.action_confirm()
            picking.button_validate()

        counterpart = rc.records
        self.assertEqual(len(counterpart), 1)
        self.assertEqual(counterpart.intercompany_parent_id, picking)
        self.assertEqual(picking.intercompany_child_ids, counterpart)
        self.assertTrue(picking.has_counterpart)
        self.assertTrue(counterpart.has_counterpart)
        self.assertEqual(len(counterpart.move_ids), len(picking.move_ids))
        for cp_move, move in zip(counterpart.move_ids, picking.move_ids, strict=False):
            self.assertEqual(cp_move.intercompany_origin_move_id, move)
        self.assertEqual(len(counterpart.move_line_ids), len(picking.move_line_ids))
        for cp_line, line in zip(
            counterpart.move_line_ids, picking.move_line_ids, strict=False
        ):
            self.assertEqual(cp_line.intercompany_origin_line_id, line)

    def test_picking_creation_same_company(self):
        """A delivery to a partner that is not an intercompany partner
        must not trigger any counterpart creation."""
        regular_partner = self.env["res.partner"].create({"name": "External Partner"})
        picking = self._make_picking(
            self.company1,
            regular_partner,
            self.picking_type_out_company1,
            self.stock_location,
            self.env.ref("stock.stock_location_customers"),
        )
        picking.action_confirm()
        picking.button_validate()

        self.assertFalse(picking.has_counterpart)

    def test_picking_creation_in(self):
        """Validating a delivery toward company2 must create one receipt
        in company2 (mode 'in', the default)."""
        self.assertEqual(
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search_count([("picking_type_id", "=", self.picking_type_in_company2.id)]),
            0,
        )
        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_out_company1,
            self.stock_location,
            self.env.ref("stock.stock_location_customers"),
        )
        picking.action_confirm()
        picking.button_validate()

        self.assertTrue(picking.is_locked)
        self.assertTrue(picking.has_counterpart)

        counterpart = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_in_company2.id)])
        )
        self.assertEqual(len(counterpart), 1)
        self.assertNotEqual(counterpart, picking)
        self.assertEqual(counterpart.intercompany_parent_id, picking)
        self.assertEqual(picking.intercompany_child_ids[0], counterpart)
        self.assertEqual(
            counterpart.location_id, self.env.ref("stock.stock_location_suppliers")
        )
        self.assertEqual(counterpart.location_dest_id, self.stock_location2)

    def test_picking_creation_out(self):
        """In mode 'out', validating a reception from company2 and clicking
        'Create Counterpart' must create one delivery in company2."""
        self.company2.intercompany_picking_creation_mode = "out"
        self.assertEqual(
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search_count(
                [("picking_type_id", "=", self.picking_type_out_company2.id)]
            ),
            0,
        )
        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        picking.action_confirm()
        picking.action_create_counterpart()

        self.assertTrue(picking.is_locked)
        self.assertTrue(picking.has_counterpart)

        counterpart = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_out_company2.id)])
        )
        self.assertEqual(len(counterpart), 1)
        self.assertNotEqual(counterpart, picking)
        self.assertEqual(counterpart.intercompany_parent_id, picking)
        self.assertEqual(picking.intercompany_child_ids[0], counterpart)
        self.assertEqual(counterpart.location_id, self.stock_location2)
        self.assertEqual(
            counterpart.location_dest_id,
            self.env.ref("stock.stock_location_customers"),
        )

    def test_picking_creation_in_wrong_mode(self):
        """In mode 'out', a delivery must not trigger a receipt counterpart."""
        self.company2.intercompany_picking_creation_mode = "out"
        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_out_company1,
            self.stock_location,
            self.env.ref("stock.stock_location_customers"),
        )
        picking.action_confirm()
        picking.button_validate()
        picking.action_create_counterpart()

        counterpart = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_in_company2.id)])
        )
        self.assertEqual(len(counterpart), 0)

    def test_picking_creation_out_wrong_mode(self):
        """In mode 'in' (default), a reception must not auto-trigger a delivery
        counterpart (it requires a manual action or scheduled action)."""
        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        picking.action_confirm()
        # No call to action_create_counterpart — must stay silent.

        counterpart = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company2.id)
            .with_user(self.user_demo)
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_out_company2.id)])
        )
        self.assertEqual(len(counterpart), 0)

    def test_picking_creation_mode_both(self):
        """In mode 'both', a delivery triggers a receipt AND a reception triggers
        a delivery (via manual action)."""
        self.company2.intercompany_picking_creation_mode = "both"

        picking_out = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_out_company1,
            self.stock_location,
            self.env.ref("stock.stock_location_customers"),
        )
        picking_in = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        picking_out.action_confirm()
        picking_out.button_validate()
        picking_in.action_confirm()
        picking_in.action_create_counterpart()

        counterpart_in = (
            self.env["stock.picking"]
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_in_company2.id)])
        )
        counterpart_out = (
            self.env["stock.picking"]
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_out_company2.id)])
        )
        self.assertEqual(len(counterpart_in), 1)
        self.assertEqual(len(counterpart_out), 1)
        self.assertEqual(counterpart_in.intercompany_parent_id, picking_out)
        self.assertEqual(counterpart_out.intercompany_parent_id, picking_in)
        self.assertEqual(picking_out.intercompany_child_ids[0], counterpart_in)
        self.assertEqual(picking_in.intercompany_child_ids[0], counterpart_out)

    def test_picking_creation_mode_none(self):
        """With no mode set, no counterpart is created in either direction."""
        self.company2.intercompany_picking_creation_mode = False

        picking_out = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_out_company1,
            self.stock_location,
            self.env.ref("stock.stock_location_customers"),
        )
        picking_in = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        picking_out.action_confirm()
        picking_out.button_validate()
        picking_in.action_confirm()
        picking_in.action_create_counterpart()

        self.assertEqual(
            self.env["stock.picking"]
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

    def test_cancel_propagates_to_child(self):
        """Cancelling a picking with an intercompany child must also cancel
        the child."""
        self.company2.intercompany_picking_creation_mode = "out"
        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        picking.action_confirm()
        picking.action_create_counterpart()

        counterpart = (
            self.env["stock.picking"]
            .sudo()
            .search([("picking_type_id", "=", self.picking_type_out_company2.id)])
        )
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")
        self.assertEqual(counterpart.state, "cancel")

    def test_no_unlock_after_counterpart_creation(self):
        """A locked picking with a counterpart cannot be unlocked."""
        self.company2.intercompany_picking_creation_mode = "out"
        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        picking.action_confirm()
        self.assertTrue(picking.is_locked)
        picking.action_toggle_is_locked()
        self.assertFalse(picking.is_locked)

        picking.action_create_counterpart()
        self.assertTrue(picking.is_locked)
        self.assertTrue(picking.has_counterpart)
        with self.assertRaises(UserError):
            picking.action_toggle_is_locked()

    def test_no_move_grouping_after_counterpart_creation(self):
        """New moves must not be grouped into a picking that already has
        an intercompany counterpart."""
        self.company2.intercompany_picking_creation_mode = "out"
        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        picking.action_confirm()
        self.assertEqual(len(picking.move_ids), 1)

        # Add a second move — before counterpart creation it groups into picking.
        ml2 = self.env["stock.move.line"].create(
            {
                "company_id": picking.company_id.id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.stock_location.id,
                "product_id": self.product2.id,
                "product_uom_id": self.uom_unit.id,
                "quantity": 2.0,
            }
        )
        move2 = self.env["stock.move"].create(
            {
                "name": "Move:" + ml2.product_id.display_name,
                "product_id": ml2.product_id.id,
                "product_uom_qty": ml2.quantity,
                "product_uom": ml2.product_uom_id.id,
                "location_id": ml2.location_id.id,
                "location_dest_id": ml2.location_dest_id.id,
                "picking_type_id": picking.picking_type_id.id,
                "company_id": picking.company_id.id,
                "partner_id": picking.partner_id.id,
                "move_line_ids": [(4, ml2.id)],
            }
        )
        move2._action_confirm()
        self.assertEqual(move2.picking_id, picking)
        self.assertEqual(len(picking.move_ids), 2)

        picking.action_create_counterpart()
        self.assertTrue(picking.has_counterpart)

        # After counterpart creation, a new move must NOT be merged into picking.
        ml3 = self.env["stock.move.line"].create(
            {
                "company_id": picking.company_id.id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.stock_location.id,
                "product_id": self.product3.id,
                "product_uom_id": self.uom_unit.id,
                "quantity": 3.0,
            }
        )
        move3 = self.env["stock.move"].create(
            {
                "name": "Move:" + ml3.product_id.display_name,
                "product_id": ml3.product_id.id,
                "product_uom_qty": ml3.quantity,
                "product_uom": ml3.product_uom_id.id,
                "location_id": ml3.location_id.id,
                "location_dest_id": ml3.location_dest_id.id,
                "picking_type_id": picking.picking_type_id.id,
                "company_id": picking.company_id.id,
                "partner_id": picking.partner_id.id,
                "move_line_ids": [(4, ml3.id)],
            }
        )
        move3._action_confirm()
        self.assertNotEqual(move3.picking_id, picking)
        self.assertEqual(len(picking.move_ids), 2)

    def test_remaining_out_counterpart_filter(self):
        """The scheduled-action domain must return only eligible reception
        pickings and exclude already-counterparted ones."""
        self.company2.intercompany_picking_creation_mode = "out"
        self.assertEqual(
            len(self.env["stock.picking"]._remaining_out_counterpart_picking()), 0
        )

        eligible = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        eligible.action_confirm()

        # A delivery (wrong direction) must not appear.
        wrong_way = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_out_company1,
            self.stock_location,
            self.env.ref("stock.stock_location_customers"),
        )
        wrong_way.action_confirm()

        # A second eligible picking without a move line yet.
        simple_eligible = (
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

        # A picking that already has a counterpart must be excluded.
        already_done = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_in_company1,
            self.env.ref("stock.stock_location_suppliers"),
            self.stock_location,
        )
        already_done.action_confirm()
        already_done.action_create_counterpart()

        remaining = self.env["stock.picking"]._remaining_out_counterpart_picking()
        self.assertEqual(remaining, eligible | simple_eligible)

        self.env["stock.picking"]._create_remaining_out_counterpart()
        self.assertTrue(eligible.has_counterpart)
        self.assertTrue(simple_eligible.has_counterpart)
        self.assertFalse(wrong_way.has_counterpart)


@tagged("post_install", "-at_install")
class TestIntercompanySyncOptions(TestIntercompanyCommon):
    """Tests for the optional sync features: intercompany_sync_qty_done
    and intercompany_share_lot."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_serial = cls.env["product.product"].create(
            {
                "name": "Product Serial",
                "type": "consu",
                "is_storable": True,
                "tracking": "serial",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )
        cls.product_lot = cls.env["product.product"].create(
            {
                "name": "Product Lot",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )
        cls.lot_serial = (
            cls.env["stock.lot"]
            .sudo()
            .create(
                {
                    "name": "SN001",
                    "product_id": cls.product_serial.id,
                    "company_id": cls.company1.id,
                }
            )
        )
        cls.lot_tracked = (
            cls.env["stock.lot"]
            .sudo()
            .create(
                {
                    "name": "LOT001",
                    "product_id": cls.product_lot.id,
                    "company_id": cls.company1.id,
                }
            )
        )

    def _make_out_picking_with_lot(self, lot, product, qty=1.0):
        """Create a delivery from company1 to company2 with a specific lot."""
        custs_location = self.env.ref("stock.stock_location_customers")
        custs_location.sudo().company_id = False
        picking = (
            self.env["stock.picking"]
            .with_context(default_company_id=self.company1.id)
            .with_user(self.user_demo)
            .create(
                {
                    "partner_id": self.company2.partner_id.id,
                    "picking_type_id": self.picking_type_out_company1.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": custs_location.id,
                }
            )
        )
        self.env["stock.move.line"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": custs_location.id,
                "product_id": product.id,
                "product_uom_id": self.uom_unit.id,
                "quantity": qty,
                "lot_id": lot.id,
                "picking_id": picking.id,
            }
        )
        return picking

    def test_sync_qty_done_disabled(self):
        """Without intercompany_sync_qty_done, the counterpart move lines keep
        their own quantity (0 or whatever Odoo sets at confirmation)."""
        self.company2.intercompany_sync_qty_done = False

        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_out_company1,
            self.stock_location,
            self.env.ref("stock.stock_location_customers"),
            qty=5.0,
        )
        picking.action_confirm()
        picking.button_validate()

        counterpart = (
            self.env["stock.picking"]
            .sudo()
            .search([("intercompany_parent_id", "=", picking.id)])
        )
        self.assertEqual(len(counterpart), 1)
        # Quantities on counterpart move lines must not be copied from origin.
        for cp_line in counterpart.move_line_ids:
            origin_line = cp_line.intercompany_origin_line_id
            if origin_line:
                self.assertNotEqual(
                    cp_line.quantity,
                    origin_line.quantity,
                    "quantity must NOT be synced when intercompany_sync_qty_done "
                    "is False.",
                )

    def test_sync_qty_done_enabled(self):
        """With intercompany_sync_qty_done enabled, done quantities from the
        origin picking are copied to the counterpart move lines."""
        self.company2.intercompany_sync_qty_done = True

        picking = self._make_picking(
            self.company1,
            self.company2.partner_id,
            self.picking_type_out_company1,
            self.stock_location,
            self.env.ref("stock.stock_location_customers"),
            qty=5.0,
        )
        picking.action_confirm()
        picking.button_validate()

        counterpart = (
            self.env["stock.picking"]
            .sudo()
            .search([("intercompany_parent_id", "=", picking.id)])
        )
        self.assertEqual(len(counterpart), 1)
        for cp_line in counterpart.move_line_ids:
            origin_line = cp_line.intercompany_origin_line_id
            if origin_line:
                self.assertEqual(
                    cp_line.quantity,
                    origin_line.quantity,
                    "quantity must match origin when intercompany_sync_qty_done "
                    "is True.",
                )

    def test_share_lot_disabled(self):
        """Without intercompany_share_lot, the lot keeps its company_id and
        is not shared; the counterpart move lines have no lot assigned."""
        self.company2.intercompany_share_lot = False
        self.lot_serial.sudo().company_id = self.company1

        picking = self._make_out_picking_with_lot(self.lot_serial, self.product_serial)
        picking.action_confirm()
        picking.button_validate()

        # Lot must still belong to company1.
        self.assertEqual(self.lot_serial.sudo().company_id, self.company1)

        counterpart = (
            self.env["stock.picking"]
            .sudo()
            .search([("intercompany_parent_id", "=", picking.id)])
        )
        self.assertEqual(len(counterpart), 1)
        for cp_line in counterpart.move_line_ids:
            self.assertNotEqual(
                cp_line.lot_id,
                self.lot_serial,
                "The same lot shouldn't be assigned on counterpart when share_lot "
                "is False.",
            )

    def test_share_lot_enabled_serial(self):
        """With intercompany_share_lot enabled, a serial-tracked lot is made
        company-independent (company_id=False) and assigned to the counterpart
        move line with the same lot record."""
        self.company2.intercompany_share_lot = True
        self.lot_serial.sudo().company_id = self.company1

        picking = self._make_out_picking_with_lot(self.lot_serial, self.product_serial)
        picking.action_confirm()
        picking.button_validate()

        # Lot must now be company-independent.
        self.assertFalse(
            self.lot_serial.sudo().company_id,
            "Lot must have company_id=False after share_lot.",
        )

        counterpart = (
            self.env["stock.picking"]
            .sudo()
            .search([("intercompany_parent_id", "=", picking.id)])
        )
        self.assertEqual(len(counterpart), 1)
        cp_lines_with_lot = counterpart.move_line_ids.filtered("lot_id")
        self.assertEqual(len(cp_lines_with_lot), 1)
        self.assertEqual(
            cp_lines_with_lot.lot_id,
            self.lot_serial,
            "Counterpart must reference the same shared lot record.",
        )

    def test_share_lot_enabled_lot_tracking(self):
        """Same as test_share_lot_enabled_serial but for lot-tracked products."""
        self.company2.intercompany_share_lot = True
        self.lot_tracked.sudo().company_id = self.company1

        picking = self._make_out_picking_with_lot(
            self.lot_tracked, self.product_lot, qty=3.0
        )
        picking.action_confirm()
        picking.button_validate()

        self.assertFalse(self.lot_tracked.sudo().company_id)

        counterpart = (
            self.env["stock.picking"]
            .sudo()
            .search([("intercompany_parent_id", "=", picking.id)])
        )
        self.assertEqual(len(counterpart), 1)
        cp_lines_with_lot = counterpart.move_line_ids.filtered("lot_id")
        self.assertTrue(cp_lines_with_lot)
        for cp_line in cp_lines_with_lot:
            self.assertEqual(cp_line.lot_id, self.lot_tracked)

    def test_share_lot_already_shared(self):
        """Calling _share_lot on an already-shared lot must be idempotent."""
        self.company2.intercompany_share_lot = True
        self.lot_serial.sudo().company_id = False  # already shared

        picking = self._make_out_picking_with_lot(self.lot_serial, self.product_serial)
        picking.action_confirm()
        picking.button_validate()

        self.assertFalse(self.lot_serial.sudo().company_id)
        counterpart = (
            self.env["stock.picking"]
            .sudo()
            .search([("intercompany_parent_id", "=", picking.id)])
        )
        cp_lines_with_lot = counterpart.move_line_ids.filtered("lot_id")
        self.assertEqual(len(cp_lines_with_lot), 1)
        self.assertEqual(cp_lines_with_lot.lot_id, self.lot_serial)
