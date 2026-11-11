# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.purchase_sale_inter_company.tests import (
    test_inter_company_purchase_sale as test_icps,
)

TestPurchaseSaleInterCompany = test_icps.TestPurchaseSaleInterCompany


class TestPurchaseSaleStockInterCompanyMrp(TestPurchaseSaleInterCompany):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create Kit and Components
        cls.kit_product = cls.env["product.product"].create(
            {"name": "Kit Product", "is_storable": False}
        )
        cls.component_1 = cls.env["product.product"].create(
            {"name": "Component 1", "is_storable": True}
        )
        cls.component_2 = cls.env["product.product"].create(
            {"name": "Component 2", "is_storable": True}
        )
        cls.component_3 = cls.env["product.product"].create(
            {"name": "Component 3", "is_storable": True}
        )
        cls.uom_box = cls.env["uom.uom"].create(
            {
                "name": "Box (10 Units)",
                "category_id": cls.env.ref("uom.product_uom_categ_unit").id,
                "factor": 0.1,
                "uom_type": "bigger",
                "rounding": 0.01,
            }
        )
        cls.partner_company_a.company_id = False
        cls.partner_company_b.company_id = False
        # One unit of component_1 and two of component_2 per kit.
        cls.bom = cls._create_bom(
            cls.kit_product,
            cls.company_b,
            [(cls.component_1, 1.0), (cls.component_2, 2.0)],
        )
        # Create PO
        po = Form(cls.env["purchase.order"])
        po.company_id = cls.company_a
        po.partner_id = cls.partner_company_b
        with po.order_line.new() as line_form:
            line_form.product_id = cls.kit_product
            line_form.product_qty = 3.0
            line_form.price_unit = 450.0
        cls.kit_po = po.save()

    @classmethod
    def _create_bom(cls, product, company, lines, product_qty=1.0, sequence=None):
        """Create a phantom BOM; lines are (product, qty[, uom]) tuples."""
        bom = Form(cls.env["mrp.bom"])
        bom.company_id = company
        bom.product_id = product
        bom.product_tmpl_id = product.product_tmpl_id
        bom.type = "phantom"
        bom.product_qty = product_qty
        for line_product, line_qty, *line_uom in lines:
            with bom.bom_line_ids.new() as line_form:
                line_form.product_id = line_product
                line_form.product_qty = line_qty
                if line_uom:
                    line_form.product_uom_id = line_uom[0]
        bom = bom.save()
        if sequence is not None:
            # Use sequence=0 for kit product to use a new bom instead of cls.bom
            bom.sequence = sequence
        return bom

    def _approve_kit_po(self, po=None):
        """Approve the PO and return the delivery picking of its sale."""
        po = po or self.kit_po
        po.with_user(self.user_company_a).button_approve()
        sale = (
            self.env["sale.order"]
            .with_user(self.user_company_b)
            .search([("auto_purchase_order_id", "=", po.id)])
        )
        return sale.picking_ids[0]

    def _set_done(self, picking, quantities):
        """Set the done quantity of each move by product."""
        for product, quantity in quantities.items():
            picking.move_ids.filtered(
                lambda m, p=product: m.product_id == p
            )._set_quantity_done(quantity)

    def _validate_without_backorder(self, picking):
        picking.with_context(
            skip_backorder=True, picking_ids_not_to_backorder=picking.ids
        ).button_validate()

    def _set_all_done(self, picking):
        for move in picking.move_ids:
            move._set_quantity_done(move.product_uom_qty)

    def _assert_quantities(self, picking, expected, field="quantity"):
        for product, quantity in expected.items():
            moves = picking.move_ids.filtered(lambda m, p=product: m.product_id == p)
            self.assertAlmostEqual(sum(moves.mapped(field)), quantity)

    def _enable_sync_picking(self):
        self.company_a.sync_picking = True
        self.company_b.sync_picking = True
        interco_location = self.env.ref("stock.stock_location_inter_company")
        self.company_a._set_per_company_inter_company_locations(interco_location)

    def _get_return_wizard(self, sale_picking):
        return self.env["stock.return.picking"].create({"picking_id": sale_picking.id})

    def _create_returns(self, sale_picking, po=None, quantities=None):
        return_wizard = self._get_return_wizard(sale_picking)
        if quantities is None:
            action = return_wizard.action_create_returns_all()
        else:
            for product, quantity in quantities.items():
                return_wizard.product_return_moves.filtered(
                    lambda line, p=product: line.product_id == p
                ).quantity = quantity
            action = return_wizard.action_create_returns()
        sale_return = self.env["stock.picking"].browse(action["res_id"])
        purchase_picking = (po or self.kit_po).picking_ids[0]
        return sale_return, purchase_picking.return_ids

    def _set_return_done(self, sale_return):
        for move in sale_return.move_ids:
            move._set_quantity_done(move.product_uom_qty)

    def _assert_user_error(self, func, message):
        with self.assertRaises(UserError) as error:
            func()
        self.assertIn(message, str(error.exception))

    def _create_bom_quantity_boms(self):
        """BOMs with different quantities on each side.

        - Sale BOM (product_qty 2): 2 x component_1, 4 x component_2
          -> 1 and 2 per kit
        - Purchase BOM (product_qty 3): 3 x component_1, 6 x component_2,
          9 x component_3 -> 1, 2 and 3 per kit
        """
        self._create_bom(
            self.kit_product,
            self.company_b,
            [(self.component_1, 2.0), (self.component_2, 4.0)],
            product_qty=2.0,
            sequence=0,
        )
        self._create_bom(
            self.kit_product,
            self.company_a,
            [(self.component_1, 3.0), (self.component_2, 6.0), (self.component_3, 9.0)],
            product_qty=3.0,
        )

    def _create_nested_kit_boms(self):
        """Nested BOMs for the kit.

        - Sale BOM: kit = 1 x sub-kit + 1 x component_1
          sub-kit BOM = 1 x component_1 + 2 x component_2
        - Purchase BOM: kit = 1 x sub-kit + 1 x component_2
          sub-kit BOM = 3 x component_1 + 4 x component_3
        """
        sub_kit = self.env["product.product"].create(
            {"name": "Sub Kit", "is_storable": True}
        )
        self._create_bom(
            self.kit_product,
            self.company_b,
            [(sub_kit, 1.0), (self.component_1, 1.0)],
            sequence=0,
        )
        self._create_bom(
            sub_kit, self.company_b, [(self.component_1, 1.0), (self.component_2, 2.0)]
        )
        self._create_bom(
            self.kit_product, self.company_a, [(sub_kit, 1.0), (self.component_2, 1.0)]
        )
        self._create_bom(
            sub_kit, self.company_a, [(self.component_1, 3.0), (self.component_3, 4.0)]
        )

    def test_sale_kit(self):
        """BOM only on the sale side"""
        sale_picking = self._approve_kit_po()
        self.assertEqual(len(sale_picking.move_ids), 2)
        # Deliver the 3 kits
        self._set_done(sale_picking, {self.component_1: 3.0, self.component_2: 6.0})
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 1)
        self.assertEqual(purchase_picking.move_ids.quantity, 3.0)

    def test_sale_kit_order_in_dozens(self):
        self.env["ir.config_parameter"].sudo().set_param("stock.propagate_uom", "1")
        self.kit_po.order_line.write(
            {"product_uom": self.env.ref("uom.product_uom_dozen").id, "product_qty": 2}
        )
        sale_picking = self._approve_kit_po()
        self._set_done(sale_picking, {self.component_1: 12.0, self.component_2: 24.0})
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertAlmostEqual(purchase_picking.move_ids.quantity, 1.0)

    def test_sale_kit_component_on_two_move_lines(self):
        sale_picking = self._approve_kit_po()
        component_2_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_2
        )
        move_line_vals = component_2_move._prepare_move_line_vals()
        component_2_move.move_line_ids = [
            Command.clear(),
            Command.create(dict(move_line_vals, quantity=2)),
            Command.create(dict(move_line_vals, quantity=2)),
        ]
        self._set_done(sale_picking, {self.component_1: 2.0})
        sale_picking.move_ids.picked = True
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertAlmostEqual(purchase_picking.move_ids.quantity, 2.0)

    def test_sale_kit_bom_replaced_before_delivery(self):
        sale_picking = self._approve_kit_po()
        self.bom.active = False
        self._create_bom(
            self.kit_product, self.company_b, [(self.component_1, 2.0)], sequence=0
        )
        self._set_done(sale_picking, {self.component_1: 2.0, self.component_2: 4.0})
        self._assert_user_error(
            lambda: self._validate_without_backorder(sale_picking), "BOM changed"
        )

    def test_sale_kit_components_split_over_backorder(self):
        self._enable_sync_picking()
        sale_picking = self._approve_kit_po()
        self._set_done(sale_picking, {self.component_1: 3.0, self.component_2: 2.0})
        sale_picking.with_context(skip_backorder=True).button_validate()
        backorder = sale_picking.backorder_ids
        self.assertEqual(backorder.move_ids.product_id, self.component_2)
        self._set_done(backorder, {self.component_2: 4.0})
        backorder.button_validate()
        self.assertEqual(self.kit_po.order_line.qty_received, 3.0)

    def test_sale_kit_two_pending_receipt_moves(self):
        sale_picking = self._approve_kit_po()
        purchase_move = self.kit_po.picking_ids[0].move_ids
        purchase_move.product_uom_qty = 2.0
        purchase_move.copy({"product_uom_qty": 1.0})._action_confirm(merge=False)
        self.assertEqual(len(self.kit_po.picking_ids[0].move_ids), 2)
        self._set_done(sale_picking, {self.component_1: 2.0, self.component_2: 4.0})
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertAlmostEqual(sum(purchase_picking.move_ids.mapped("quantity")), 2.0)

    def test_purchase_kit_pending_move_without_bom_line(self):
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        component_move = self.kit_po.picking_ids[0].move_ids[0]
        component_move.copy({"bom_line_id": False})._action_confirm(merge=False)
        sale_picking.move_ids._set_quantity_done(2.0)
        self._assert_user_error(
            lambda: self._validate_without_backorder(sale_picking), "BOM changed"
        )

    def test_sale_kit_bom_archived_before_delivery(self):
        sale_picking = self._approve_kit_po()
        self.bom.active = False
        self._set_done(sale_picking, {self.component_1: 2.0, self.component_2: 4.0})
        self._assert_user_error(
            lambda: self._validate_without_backorder(sale_picking), "BOM changed"
        )

    def test_sale_kit_partial(self):
        sale_picking = self._approve_kit_po()
        self.assertEqual(len(sale_picking.move_ids), 2)
        # Deliver only 2 kits
        self._set_done(sale_picking, {self.component_1: 2.0, self.component_2: 4.0})
        sale_picking.with_context(skip_backorder=True).button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 1)
        self.assertEqual(purchase_picking.move_ids.quantity, 2.0)

    def test_sale_kit_missing_component_no_backorder(self):
        sale_picking = self._approve_kit_po()
        self._set_done(sale_picking, {self.component_1: 3.0})
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(purchase_picking.move_ids.quantity, 0.0)

    def test_purchase_kit_partial(self):
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        self.assertEqual(len(sale_picking.move_ids), 1)
        # Deliver only 2 kits
        sale_picking.move_ids._set_quantity_done(2.0)
        sale_picking.with_context(skip_backorder=True).button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 2)
        self._assert_quantities(
            purchase_picking, {self.component_1: 2.0, self.component_2: 4.0}
        )

    def test_purchase_kit_validated_by_sale_user(self):
        self.bom.write({"company_id": self.company_a.id})
        self.user_company_b.groups_id |= self.env.ref("stock.group_stock_user")
        sale_picking = self._approve_kit_po().with_user(self.user_company_b)
        sale_picking.move_ids._set_quantity_done(2.0)
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        self._assert_quantities(
            purchase_picking, {self.component_1: 2.0, self.component_2: 4.0}
        )

    def test_purchase_kit_sync_picking(self):
        """With sync_picking enabled, validating the delivery must also
        validate the receipt of the kit components."""
        self.company_a.sync_picking = True
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(purchase_picking.state, "done")

    def test_sale_purchase_kit(self):
        """2 different BOMs on each side for the same kit product"""
        self._create_bom(
            self.kit_product,
            self.company_a,
            [(self.component_1, 1.0), (self.component_2, 2.0), (self.component_3, 3.0)],
        )
        sale_picking = self._approve_kit_po()
        self.assertEqual(len(sale_picking.move_ids), 2)
        # Deliver 2 of the 3 kits
        self._set_done(sale_picking, {self.component_1: 2.0, self.component_2: 4.0})
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(len(purchase_picking.move_ids), 3)
        self._assert_quantities(
            purchase_picking,
            {self.component_1: 2.0, self.component_2: 4.0, self.component_3: 6.0},
        )

    def test_sale_purchase_kit_bom_quantity(self):
        """A BOM quantity greater than one must not be mistaken for a kit
        quantity when computing and exploding the kits."""
        self._create_bom_quantity_boms()
        # Sell four kits, i.e. two applications of the sale BOM.
        self.kit_po.order_line.product_qty = 4.0
        sale_picking = self._approve_kit_po()
        self._assert_quantities(
            sale_picking,
            {self.component_1: 4.0, self.component_2: 8.0},
            "product_uom_qty",
        )
        # Deliver 2 of the 4 kits
        self._set_done(sale_picking, {self.component_1: 2.0, self.component_2: 4.0})
        self._validate_without_backorder(sale_picking)
        # The reception of the two kits requires 2, 4 and 6 purchase units.
        purchase_picking = self.kit_po.picking_ids[0]
        self._assert_quantities(
            purchase_picking,
            {self.component_1: 2.0, self.component_2: 4.0, self.component_3: 6.0},
        )

    def test_nested_kit_sync(self):
        """Nested phantom BOMs must be exploded from the kit BOM, not from
        the sub-BOM of the first component move."""
        self._create_nested_kit_boms()
        # Sell two kits.
        self.kit_po.order_line.product_qty = 2.0
        sale_picking = self._approve_kit_po()
        # The component moves belong to the sale BOM and to its sub-BOM.
        self.assertEqual(len(sale_picking.move_ids.bom_line_id.bom_id), 2)
        # Deliver 1 of the 2 kits
        for move in sale_picking.move_ids:
            move._set_quantity_done(move.product_uom_qty / 2)
        self._validate_without_backorder(sale_picking)

        # One kit: 1 + 1 component_1 on the sale side.
        self._assert_quantities(sale_picking, {self.component_1: 2.0})
        purchase_picking = self.kit_po.picking_ids[0]

        # One kit requires 3 and 4 units through the sub-kit, plus 1
        # component_2 on the top-level BOM.
        self._assert_quantities(
            purchase_picking,
            {self.component_1: 3.0, self.component_2: 1.0, self.component_3: 4.0},
        )

    def test_tracked_nested_kit_component(self):
        """A tracked component inside a nested BOM must be rejected."""
        self._create_nested_kit_boms()
        # component_3 only appears in the purchase sub-BOM, not in the
        # top-level BOM lines.
        self.component_3.tracking = "lot"
        self.kit_po.order_line.product_qty = 2.0
        sale_picking = self._approve_kit_po()
        self._set_all_done(sale_picking)
        self._assert_user_error(sale_picking.button_validate, "tracked products")

    def test_purchase_kit_other_uoms(self):
        """The kit quantities must be converted between the BOM, its lines
        and the product UoMs when syncing the destination picking."""
        # Express the kit BOM in boxes of 10 units: one box (10 kits)
        # requires 10 units of component 1 and 1 box of component 2, i.e. 1
        # unit of each per kit.
        self.bom.write(
            {"company_id": self.company_a.id, "product_uom_id": self.uom_box.id}
        )
        line_1 = self.bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.component_1
        )
        line_2 = self.bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.component_2
        )
        line_1.product_qty = 10.0
        line_2.product_qty = 1.0
        line_2.product_uom_id = self.uom_box
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(2.0)
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        # 2 kits = 0.2 box: 2 units of component 1 and 0.2 box of component 2.
        self._assert_quantities(
            purchase_picking, {self.component_1: 2.0, self.component_2: 0.2}
        )
        # 0.3 box is 3 units of component_2
        self.assertAlmostEqual(
            purchase_picking.move_ids.filtered(
                lambda m: m.product_id == self.component_2
            ).product_qty,
            3.0,
        )

    def test_purchase_kit_order_in_dozens(self):
        self.env["ir.config_parameter"].sudo().set_param("stock.propagate_uom", "1")
        self.bom.write({"company_id": self.company_a.id})
        self.kit_po.order_line.write(
            {"product_uom": self.env.ref("uom.product_uom_dozen").id, "product_qty": 2}
        )
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(1.0)
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        self._assert_quantities(
            purchase_picking, {self.component_1: 12.0, self.component_2: 24.0}
        )

    def test_purchase_kit_duplicate_component(self):
        """A component repeated on several BOM lines must be split per line
        instead of receiving the full quantity on each move."""
        self.bom.write({"company_id": self.company_a.id})
        self.env["mrp.bom.line"].create(
            {
                "bom_id": self.bom.id,
                "product_id": self.component_1.id,
                "product_qty": 2.0,
            }
        )
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(2.0)
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        component_1_moves = purchase_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        self.assertEqual(len(component_1_moves), 2)
        self._assert_quantities(
            purchase_picking, {self.component_1: 6.0, self.component_2: 4.0}
        )

    def test_purchase_kit_service_component(self):
        self.bom.write({"company_id": self.company_a.id})
        service = self.env["product.product"].create(
            {"name": "Assembly", "type": "service"}
        )
        self.env["mrp.bom.line"].create(
            {"bom_id": self.bom.id, "product_id": service.id, "product_qty": 1.0}
        )
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(2.0)
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        self._assert_quantities(
            purchase_picking, {self.component_1: 2.0, self.component_2: 4.0}
        )

    def test_sale_purchase_kit_optional_component(self):
        """Optional (zero-quantity) components must not change the kit
        quantity.

        component_1 is optional on the sale BOM (skipped when computing the
        delivered kits); component_2 on the purchase BOM (received at 0).
        """
        self.bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.component_1
        ).product_qty = 0.0
        self._create_bom(
            self.kit_product,
            self.company_a,
            [(self.component_1, 1.0), (self.component_2, 0.0)],
        )
        sale_picking = self._approve_kit_po()
        # On Sale side the optional component does not create a move
        self.assertEqual(len(sale_picking.move_ids), 1)
        self._set_done(sale_picking, {self.component_2: 4.0})
        self._validate_without_backorder(sale_picking)
        purchase_picking = self.kit_po.picking_ids[0]
        # On the Purchase side the optional component does create a move
        self.assertEqual(len(purchase_picking.move_ids), 2)
        self._assert_quantities(
            purchase_picking, {self.component_1: 2.0, self.component_2: 0.0}
        )

    def test_tracked_sale_kit_component(self):
        """A tracked kit component on the sale side is not supported."""
        self.component_1.tracking = "lot"
        sale_picking = self._approve_kit_po()
        self._set_done(sale_picking, {self.component_1: 3.0, self.component_2: 6.0})
        component_1_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        component_1_move.move_line_ids.lot_id = self.env["stock.lot"].create(
            {
                "name": "LOT-C1",
                "product_id": self.component_1.id,
                "company_id": self.company_b.id,
            }
        )
        self._assert_user_error(sale_picking.button_validate, "tracked products")

    def test_tracked_purchase_kit_component(self):
        """A tracked kit component on the purchase side is not supported."""
        self.bom.write({"company_id": self.company_a.id})
        self.component_2.tracking = "lot"
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        self._assert_user_error(sale_picking.button_validate, "tracked products")

    def test_tracked_sale_kit_product(self):
        """A tracked kit product on the purchase side is not supported."""
        self.kit_product.tracking = "lot"
        sale_picking = self._approve_kit_po()
        self._set_done(sale_picking, {self.component_1: 3.0, self.component_2: 6.0})
        self._assert_user_error(sale_picking.button_validate, "tracked products")

    def test_tracked_purchase_kit_product(self):
        """A tracked kit product on the sale side is not supported."""
        self.bom.write({"company_id": self.company_a.id})
        self.kit_product.tracking = "lot"
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.move_ids.move_line_ids.lot_id = self.env["stock.lot"].create(
            {
                "name": "LOT-KIT",
                "product_id": self.kit_product.id,
                "company_id": self.company_b.id,
            }
        )
        self._assert_user_error(sale_picking.button_validate, "tracked products")

    def test_sync_failure_notify(self):
        """Errors raised while syncing the kit quantities must respect the
        configured failure action."""
        self.company_a.sync_picking_failure_action = "notify"
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        with mock.patch.object(
            type(sale_picking),
            "_set_intercompany_kit_quantities_done",
            side_effect=Exception("boom"),
        ):
            sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertTrue(sale_picking.activity_ids)
        self.assertNotEqual(purchase_picking.state, "done")

    def test_purchase_kit_return(self):
        """A returned kit must sync the returned quantities on both sides,
        keeping each repeated component on its own BOM line."""
        self._enable_sync_picking()
        self.bom.write({"company_id": self.company_a.id})
        # Repeat component_1 on a second line to check the per-BOM-line split.
        self.env["mrp.bom.line"].create(
            {
                "bom_id": self.bom.id,
                "product_id": self.component_1.id,
                "product_qty": 2.0,
            }
        )
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        sale_return, purchase_return = self._create_returns(sale_picking)
        self._set_return_done(sale_return)
        sale_return.button_validate()
        component_1_moves = purchase_return.move_ids.filtered(
            lambda m: m.product_id == self.component_1
        )
        # 3 kits: component_1 on two lines (3 + 6) and component_2 (6).
        self.assertEqual(len(component_1_moves), 2)
        self._assert_quantities(
            purchase_return, {self.component_1: 9.0, self.component_2: 6.0}
        )

    def test_purchase_kit_return_by_sale_user(self):
        self._enable_sync_picking()
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        stock_user_group = self.env.ref("stock.group_stock_user")
        self.user_company_b.groups_id |= stock_user_group
        self.intercompany_sale_user_id.write(
            {
                "groups_id": [Command.link(stock_user_group.id)],
                "email": "ic@example.com",
            }
        )
        self.company_a.intercompany_sale_user_id = self.intercompany_sale_user_id
        return_wizard = (
            self.env["stock.return.picking"]
            .with_user(self.user_company_b)
            .create({"picking_id": sale_picking.id})
        )
        return_wizard.action_create_returns_all()
        purchase_return = self.kit_po.picking_ids[0].return_ids
        self._assert_quantities(
            purchase_return,
            {self.component_1: 3.0, self.component_2: 6.0},
            "product_uom_qty",
        )

    def test_tracked_kit_return(self):
        """A product tracked after the delivery must be rejected on return."""
        self._enable_sync_picking()
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        # The tracking changes after the delivery.
        self.component_2.tracking = "lot"
        return_wizard = self._get_return_wizard(sale_picking)
        self._assert_user_error(
            return_wizard.action_create_returns_all, "tracked products"
        )

    def test_sale_kit_return_bom_archived(self):
        self._enable_sync_picking()
        sale_picking = self._approve_kit_po()
        self._set_all_done(sale_picking)
        sale_picking.button_validate()
        self.bom.active = False
        return_wizard = self._get_return_wizard(sale_picking)
        self._assert_user_error(return_wizard.action_create_returns_all, "BOM changed")

    def test_sale_kit_return(self):
        """Returning part of a 'sale-kit' must return the corresponding kit
        quantity on the purchase side."""
        self._enable_sync_picking()
        sale_picking = self._approve_kit_po()
        self._set_done(sale_picking, {self.component_1: 3.0, self.component_2: 6.0})
        sale_picking.button_validate()
        purchase_picking = self.kit_po.picking_ids[0]
        self.assertEqual(purchase_picking.move_ids.product_id, self.kit_product)
        # Return only 2 of the 3 delivered kits.
        sale_return, purchase_return = self._create_returns(
            sale_picking, quantities={self.component_1: 2.0, self.component_2: 4.0}
        )
        self.assertEqual(purchase_return.move_ids.product_id, self.kit_product)
        self.assertEqual(purchase_return.move_ids.product_uom_qty, 2.0)
        self._set_return_done(sale_return)
        sale_return.button_validate()
        self.assertEqual(purchase_return.move_ids.quantity, 2.0)

    def test_sale_purchase_kit_return_bom_quantity(self):
        """Returning a 'sale-purchase-kit' must explode the purchase BOM,
        not copy the sale components quantities."""
        self._enable_sync_picking()
        self._create_bom_quantity_boms()
        # Sell four kits, i.e. two applications of the sale BOM.
        self.kit_po.order_line.product_qty = 4.0
        sale_picking = self._approve_kit_po()
        self._set_done(sale_picking, {self.component_1: 4.0, self.component_2: 8.0})
        sale_picking.button_validate()
        sale_return, purchase_return = self._create_returns(sale_picking)
        # The purchase BOM is exploded: four kits require 4, 8 and 12 units
        # of the purchase components, whereas the sale side only ships 4
        # and 8.
        expected = {
            self.component_1: 4.0,
            self.component_2: 8.0,
            self.component_3: 12.0,
        }
        self._assert_quantities(purchase_return, expected, "product_uom_qty")
        self._set_return_done(sale_return)
        sale_return.button_validate()
        self._assert_quantities(purchase_return, expected)

    def test_nested_kit_return(self):
        """Returning a nested kit must explode the purchase kit BOM."""
        self._enable_sync_picking()
        self._create_nested_kit_boms()
        # Sell two kits.
        self.kit_po.order_line.product_qty = 2.0
        sale_picking = self._approve_kit_po()
        self._set_all_done(sale_picking)
        sale_picking.button_validate()
        sale_return, purchase_return = self._create_returns(sale_picking)
        # Two kits require 6 and 8 units through the purchase sub-kit, plus
        # 2 component_2 on the top-level purchase BOM.
        expected = {self.component_1: 6.0, self.component_2: 2.0, self.component_3: 8.0}
        self._assert_quantities(purchase_return, expected, "product_uom_qty")
        self._set_return_done(sale_return)
        sale_return.button_validate()
        self._assert_quantities(purchase_return, expected)

    def test_mixed_kit_return(self):
        """A return mixing a kit and a plain product must return both."""
        self._enable_sync_picking()
        plain_product = self.env["product.product"].create(
            {"name": "Plain Product", "is_storable": True}
        )
        self.env["purchase.order.line"].create(
            {
                "order_id": self.kit_po.id,
                "product_id": plain_product.id,
                "product_qty": 2.0,
                "price_unit": 10.0,
            }
        )
        sale_picking = self._approve_kit_po()
        self._set_all_done(sale_picking)
        sale_picking.button_validate()
        _sale_return, purchase_return = self._create_returns(sale_picking)
        self._assert_quantities(
            purchase_return,
            {self.kit_product: 3.0, plain_product: 2.0},
            "product_uom_qty",
        )

    def _add_kit_po_line(self, quantity):
        self.env["purchase.order.line"].create(
            {
                "order_id": self.kit_po.id,
                "product_id": self.kit_product.id,
                "product_qty": quantity,
                "price_unit": 450.0,
            }
        )

    def test_purchase_kit_return_two_order_lines(self):
        self._enable_sync_picking()
        self.bom.write({"company_id": self.company_a.id})
        self._add_kit_po_line(2.0)
        sale_picking = self._approve_kit_po()
        self._set_all_done(sale_picking)
        sale_picking.button_validate()
        _sale_return, purchase_return = self._create_returns(sale_picking)
        self._assert_quantities(
            purchase_return,
            {self.component_1: 5.0, self.component_2: 10.0},
            "product_uom_qty",
        )

    def test_sale_kit_return_two_order_lines(self):
        self._enable_sync_picking()
        self._add_kit_po_line(2.0)
        sale_picking = self._approve_kit_po()
        self._set_all_done(sale_picking)
        sale_picking.button_validate()
        _sale_return, purchase_return = self._create_returns(sale_picking)
        self._assert_quantities(
            purchase_return, {self.kit_product: 5.0}, "product_uom_qty"
        )

    def test_mixed_kit_return_by_lot(self):
        if "lot_id" not in self.env["stock.return.picking.line"]._fields:
            self.skipTest("stock_picking_return_lot is not installed")
        self._enable_sync_picking()
        self.bom.write({"company_id": self.company_a.id})
        serial_product = self.env["product.product"].create(
            {"name": "Serial Product", "is_storable": True, "tracking": "serial"}
        )
        serial_1, serial_2 = self.env["stock.lot"].create(
            [
                {"name": "SN1", "product_id": serial_product.id, "company_id": False},
                {"name": "SN2", "product_id": serial_product.id, "company_id": False},
            ]
        )
        self.env["purchase.order.line"].create(
            {
                "order_id": self.kit_po.id,
                "product_id": serial_product.id,
                "product_qty": 2.0,
                "price_unit": 10.0,
            }
        )
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids.filtered(
            lambda m: m.product_id == self.kit_product
        )._set_quantity_done(3.0)
        serial_move = sale_picking.move_ids.filtered(
            lambda m: m.product_id == serial_product
        )
        move_line_vals = serial_move._prepare_move_line_vals()
        serial_move.move_line_ids = [
            Command.clear(),
            Command.create(dict(move_line_vals, quantity=1, lot_id=serial_1.id)),
            Command.create(dict(move_line_vals, quantity=1, lot_id=serial_2.id)),
        ]
        sale_picking.move_ids.picked = True
        sale_picking.button_validate()
        return_wizard = self._get_return_wizard(sale_picking)
        return_wizard.product_return_moves.filtered(
            lambda line: line.lot_id == serial_2
        ).unlink()
        return_wizard.action_create_returns()
        purchase_return = self.kit_po.picking_ids[0].return_ids
        self._assert_quantities(
            purchase_return,
            {self.component_1: 3.0, self.component_2: 6.0, serial_product: 1.0},
            "product_uom_qty",
        )
        self.assertEqual(
            purchase_return.move_ids.filtered(
                lambda m: m.product_id == serial_product
            ).restrict_lot_id,
            serial_1,
        )

    def test_kit_return_bom_changed(self):
        """A BOM changed since the receipt must block the kit return."""
        self._enable_sync_picking()
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        # Replace the purchase BOM: the receipt moves keep the old BOM lines.
        self.bom.active = False
        self._create_bom(self.kit_product, self.company_a, [(self.component_1, 2.0)])
        return_wizard = self._get_return_wizard(sale_picking)
        self._assert_user_error(return_wizard.action_create_returns_all, "BOM changed")

    def test_kit_return_bom_archived(self):
        self._enable_sync_picking()
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        self.bom.active = False
        return_wizard = self._get_return_wizard(sale_picking)
        self._assert_user_error(return_wizard.action_create_returns_all, "BOM changed")

    def test_kit_sync_bom_changed(self):
        """A BOM line added after the receipt must block the sync."""
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        # Add a component to the purchase BOM: the receipt has no such move.
        self.env["mrp.bom.line"].create(
            {
                "bom_id": self.bom.id,
                "product_id": self.component_3.id,
                "product_qty": 1.0,
            }
        )
        sale_picking.move_ids._set_quantity_done(3.0)
        self._assert_user_error(sale_picking.button_validate, "BOM changed")

    def test_kit_sync_bom_archived(self):
        self.bom.write({"company_id": self.company_a.id})
        sale_picking = self._approve_kit_po()
        self.bom.active = False
        sale_picking.move_ids._set_quantity_done(3.0)
        self._assert_user_error(sale_picking.button_validate, "BOM changed")

    def test_plain_product_return(self):
        """The kit return override must delegate to the base module for plain
        products."""
        self.company_a.sync_picking = True
        product = self.env["product.product"].create(
            {"name": "Plain Product", "is_storable": True}
        )
        po = Form(self.env["purchase.order"])
        po.company_id = self.company_a
        po.partner_id = self.partner_company_b
        with po.order_line.new() as line_form:
            line_form.product_id = product
            line_form.product_qty = 3.0
            line_form.price_unit = 10.0
        po = po.save()
        sale_picking = self._approve_kit_po(po)
        sale_picking.move_ids._set_quantity_done(3.0)
        sale_picking.button_validate()
        purchase_picking = po.picking_ids[0]
        self.assertEqual(purchase_picking.state, "done")
        sale_return, purchase_return = self._create_returns(sale_picking, po)
        self.assertEqual(sale_return.move_ids.product_id, product)
        self.assertEqual(purchase_return.move_ids.product_id, product)
        self.assertAlmostEqual(purchase_return.move_ids.product_uom_qty, 3.0)
